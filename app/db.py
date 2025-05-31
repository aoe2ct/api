import enum
from datetime import date
from typing import Literal

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

from .settings import settings

engine = create_engine(settings.database_url)


class SetType(enum.Enum):
    best_of = "best_of"
    play_all = "play_all"


class TournamentBase(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None)


class TournamentWithId(TournamentBase):
    id: str = Field(primary_key=True, max_length=15)


class TournamentCreate(TournamentWithId):
    stages: list["Stage"] = []


class Tournaments(TournamentWithId, table=True):
    created_by: str = Field(default=None)
    stages: list["Stage"] = Relationship()


class BaseStage(SQLModel):
    order: int = Field(primary_key=True, gt=0)
    format: str = "knockout"
    start_date: date | None = None
    end_date: date | None = None
    set_type: SetType = SetType.best_of
    set_length: int = 3
    map_draft: str | None
    civ_draft: str | None


class Stage(BaseStage, table=True):
    tournament_id: str = Field(
        max_length=15, foreign_key="tournaments.id", primary_key=True
    )


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def fix_stage(tournament: Tournaments):
    for i in range(len(tournament.stages)):
        if isinstance(tournament.stages[i].start_date, str):
            tournament.stages[i].start_date = date.fromisoformat(
                tournament.stages[i].start_date
            )
        if isinstance(tournament.stages[i].end_date, str):
            tournament.stages[i].end_date = date.fromisoformat(
                tournament.stages[i].end_date
            )
        if not isinstance(tournament.stages[i].set_type, SetType):
            tournament.stages[i].set_type = SetType(tournament.stages[i].set_type)

    return tournament
