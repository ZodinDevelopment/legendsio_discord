from typing import Optional, Literal

import hashlib
from datetime import datetime

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Float, ForeignKey, Boolean,
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship


Base = declarative_base()
engine = create_async_engine("sqlite+aiosqlite:///legends.db")
AioSession = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base.metadata.bind = engine
AioSession.configure(bind=engine)

STATUSES = {
    0: "seeking-roster",
    1: "seeking-temp",
    2: "in-roster",
    3: "training",
    4: "temp-roster"
}
STATUSES = list(STATUSES.values())

ROSTER_STATUSES = [
    "new-recruiting",
    "recruiting-preseason",
    "recruiting-midseason",
    "recruiting-temp",
    "training",
    "full-perm",
    "full-temp"
]

class Roster(Base):
    __tablename__ = "roster"
    id = Column(Integer, primary_key=True)
    team_name = Column(String(32))
    org_name = Column(String(32))
    timezone = Column(String(3), default="CST")
    roster_status = Column(Integer, default=0)

    coach_id = Column(ForeignKey("coach.id"))
    coach = relationship("Coach", back_populates="rosters")

    players = relationship("Agent", back_populates="roster")
    avg_member_mmr = Column(Float, nullable=True)



class Coach(Base):
    __tablename__ = "coach"
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    name = Column(String(32), nullable=True)
    joined_at = Column(DateTime, index=True)
    twitter_at_name = Column(String(32), unique=True)

    rosters = relationship("Roster", back_populates="coach")
    avg_player_mmr = Column(Float, nullable=True)



class Agent(Base):
    __tablename__ = "agent"
    id = Column(BigInteger, primary_key=True, autoincrement=False)  # discord id
    guild_id = Column(BigInteger)
    activision_id = Column(String(32), index=True, unique=True)
    joined_at = Column(DateTime, index=True)
    agent_status = Column(Integer, index=True, default=0)
    player_division = Column(String, index=True, default="Unranked")
    mmr = Column(Float, default=25.0)
    arena_killcount = Column(Integer, default=0)
    arena_deathcount = Column(Integer, default=0)
    arena_victories = Column(Integer, default=0)
    player_role = Column(String, default="Flex")
    utc_offset = Column(Integer, default=-5)
    passcode_hash = Column(String(128))

    roster_id = Column(ForeignKey("roster.id"))
    roster = relationship("Roster", back_populates="players")

    coach_id = Column(ForeignKey("coach.id"))
    coach = relationship("Coach", back_populates="agents")

    def __init__(
            self,
            *,
            discord_id: int,
            guild_id: int,
            activision_id: str,
            agent_status: Literal["seeking-roster", "seeking-temp", "in-roster", "training", "temp-roster"],
            player_role: Literal["Flex", "Main AR", "2nd AR", "Main Sub", "Obj Sub"],
            passcode: int,
            utc_offset: Optional[int],
            roster: Optional[Roster],
            coach: Optional[Coach]
    ):
        now = datetime.utcnow()
        self.id = discord_id
        self.guild_id = guild_id
        self.joined_at = now
        self.activision_id = activision_id
        status_int = STATUSES.index(agent_status)
        self.agent_status = status_int
        self.player_role = player_role
        if len(str(passcode)) != 4:
            passcode = 0000
        self.passcode_hash = hashlib.sha256(str(passcode).encode('utf-8')).hexdigest()
        self.utc_offset = utc_offset
        self.roster = roster
        self.coach = coach


