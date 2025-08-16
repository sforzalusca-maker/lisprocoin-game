from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    username: str
    usdc_balance: float
    games_played: int
    games_won: int
    tournaments_played: int
    tournaments_won: int

class Transaction(BaseModel):
    amount: float

class TableCreate(BaseModel):
    name: str

class TableInfo(BaseModel):
    table_id: int
    name: str
    players: List[str]
    in_game: bool
    winner: Optional[str]

class TableJoin(BaseModel):
    table_id: int

class TableWinner(BaseModel):
    table_id: int
    winner: str

class TournamentCreate(BaseModel):
    name: str

class TournamentInfo(BaseModel):
    tournament_id: int
    name: str
    round: int
    players: List[str]
    eliminated: List[str]
    winner: Optional[str]

class TournamentJoin(BaseModel):
    tournament_id: int

class TournamentWinner(BaseModel):
    tournament_id: int
    winner: str
