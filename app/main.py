from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security.oauth2 import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlmodel import Session, select
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

from .db import (
    TournamentCreate,
    Tournaments,
    create_db_and_tables,
    fix_stage,
    get_session,
)
from .settings import settings


class DiscordUser(BaseModel):
    username: str
    display_name: str


config = Config(".env")
oauth = OAuth(config)
_ = oauth.register(
    name="discord",
    server_metadata_url="https://discord.com/.well-known/openid-configuration",
    client_kwargs={"scope": "identify"},
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


SessionDep = Annotated[Session, Depends(get_session)]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    response = httpx.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if not response.is_success:
        raise credentials_exception
    json = response.json()
    return DiscordUser(username=json["username"], display_name=json["global_name"])


DiscordAuth = Annotated[DiscordUser, Depends(get_current_user)]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, settings.secret_key)


@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.discord.authorize_redirect(request, redirect_uri)


@app.get("/auth")
async def auth(request: Request):
    return await oauth.discord.authorize_access_token(request)


@app.get("/users/me")
async def my_user(user: DiscordAuth):
    return user


@app.get("/tournaments")
async def list_tournaments(session: SessionDep):
    tournaments = session.exec(select(Tournaments)).all()
    return tournaments


@app.get("/tournaments/{tournament_id}")
async def get_tournament(tournament_id: str, session: SessionDep):
    tournament = session.get(Tournaments, tournament_id)
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


@app.post("/tournaments")
async def create_tournament(
    tournament: TournamentCreate, user: DiscordAuth, session: SessionDep
):
    new_tournament = fix_stage(Tournaments.model_validate(tournament))
    new_tournament.created_by = user.username
    session.add(new_tournament)
    session.commit()
    session.refresh(new_tournament)
    return new_tournament
