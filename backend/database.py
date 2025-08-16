from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lisprocoin.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

table_player_association = Table(
    'table_player_association', Base.metadata,
    Column('table_id', Integer, ForeignKey('tables.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

tournament_player_association = Table(
    'tournament_player_association', Base.metadata,
    Column('tournament_id', Integer, ForeignKey('tournaments.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    usdc_balance = Column(Float, default=0.0)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    tournaments_played = Column(Integer, default=0)
    tournaments_won = Column(Integer, default=0)

class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    in_game = Column(Boolean, default=False)
    winner = Column(String, nullable=True)
    players = relationship("User", secondary=table_player_association)

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    round = Column(Integer, default=1)
    winner = Column(String, nullable=True)
    players = relationship("User", secondary=tournament_player_association)
    eliminated = Column(String, default="") # CSV of usernames

Base.metadata.create_all(bind=engine)
