from .database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

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
    created_at = Column(DateTime, default=datetime.utcnow)

class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    in_game = Column(Boolean, default=False)
    winner = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TablePlayer(Base):
    __tablename__ = "table_players"
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("tables.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    round = Column(Integer, default=1)
    winner = Column(String, nullable=True)
    eliminated = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class TournamentPlayer(Base):
    __tablename__ = "tournament_players"
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    tx_type = Column(String)  # 'deposit', 'withdraw', 'win'
    tx_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
