from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    username: str
    usdc_balance: float
    games_played: int
    games_won: int
    tournaments_played: int
    tournaments_won: int
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TransactionCreate(BaseModel):
    amount: float

class TableCreate(BaseModel):
    name: str

class TableInfo(BaseModel):
    id: int
    name: str
    players: List[str]
    in_game: bool
    winner: Optional[str]
    created_at: datetime

class TableJoin(BaseModel):
    table_id: int

class TableWinner(BaseModel):
    table_id: int
    winner: str

class TournamentCreate(BaseModel):
    name: str

class TournamentInfo(BaseModel):
    id: int
    name: str
    round: int
    players: List[str]
    eliminated: List[str]
    winner: Optional[str]
    created_at: datetime

class TournamentJoin(BaseModel):
    tournament_id: int

class TournamentWinner(BaseModel):
    tournament_id: int
    winner: str

class PaymentResponse(BaseModel):
    status: bool
    message: str
    tx_hash: Optional[str] = None
