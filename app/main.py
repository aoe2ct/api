from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.security.oauth2 import OAuth2PasswordBearer
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field, Session, SQLModel, create_engine, select
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str
    secret_key: str
    discord_client_id: str
    discord_client_secret: str


settings = Settings()
engine = create_engine(settings.database_url)
config = Config(".env")
oauth = OAuth(config)
_ = oauth.register(
    name="discord",
    server_metadata_url="https://discord.com/.well-known/openid-configuration",
    client_kwargs={"scope": "identify"},
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_session():
    with Session(engine) as session:
        yield session


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
    return response.json()["username"]


class Tournaments(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=15)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


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
async def my_user(username: Annotated[str, Depends(get_current_user)]):
    return {"message": f"Hello {username}"}


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
async def create_tournament(tournament: Tournaments, session: SessionDep):
    session.add(tournament)
    session.commit()
    session.refresh(tournament)
    return tournament
