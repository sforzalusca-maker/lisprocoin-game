from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import SessionLocal, User
from models import (
    UserCreate, Token, UserOut, Transaction,
    TableCreate, TableInfo, TableJoin, TableWinner,
    TournamentCreate, TournamentInfo, TournamentJoin, TournamentWinner
)
from auth import verify_password, get_password_hash, create_access_token
from coinbase import send_usdc
from poker import create_table, join_table, start_table, declare_winner, list_tables
from tournament import create_tournament, join_tournament, next_round, declare_tournament_winner, list_tournaments
import os

load_dotenv()
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token error")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token error")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/register", response_model=Token)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        hashed_password=hashed_password,
        usdc_balance=0.0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        username=current_user.username,
        usdc_balance=current_user.usdc_balance,
        games_played=current_user.games_played,
        games_won=current_user.games_won,
        tournaments_played=current_user.tournaments_played,
        tournaments_won=current_user.tournaments_won
    )

@app.post("/deposit")
def deposit(transaction: Transaction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.usdc_balance += transaction.amount
    db.commit()
    return {"message": "Deposito effettuato", "usdc_balance": current_user.usdc_balance}

@app.post("/withdraw")
def withdraw(transaction: Transaction, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.usdc_balance < transaction.amount:
        raise HTTPException(status_code=400, detail="Saldo insufficiente")
    current_user.usdc_balance -= transaction.amount
    db.commit()
    return {"message": "Prelievo effettuato", "usdc_balance": current_user.usdc_balance}

@app.post("/pay_game_fee")
def pay_game_fee(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fee = float(os.getenv("GAME_FEE", "0.03"))
    if current_user.usdc_balance < fee:
        raise HTTPException(status_code=400, detail="Saldo insufficiente")
    if send_usdc(current_user.username, fee):
        current_user.usdc_balance -= fee
        current_user.games_played += 1
        db.commit()
        return {"message": "Fee pagata", "usdc_balance": current_user.usdc_balance}
    else:
        raise HTTPException(status_code=400, detail="Pagamento fallito")

@app.post("/pay_tournament_fee")
def pay_tournament_fee(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fee = float(os.getenv("TOURNAMENT_FEE", "1"))
    if current_user.usdc_balance < fee:
        raise HTTPException(status_code=400, detail="Saldo insufficiente")
    if send_usdc(current_user.username, fee):
        current_user.usdc_balance -= fee
        current_user.tournaments_played += 1
        db.commit()
        return {"message": "Fee torneo pagata", "usdc_balance": current_user.usdc_balance}
    else:
        raise HTTPException(status_code=400, detail="Pagamento fallito")

@app.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    users = db.query(User).all()
    users_out = [
        UserOut(
            username=u.username,
            usdc_balance=u.usdc_balance,
            games_played=u.games_played,
            games_won=u.games_won,
            tournaments_played=u.tournaments_played,
            tournaments_won=u.tournaments_won
        )
        for u in users
    ]
    return users_out

# ========== TAVOLI MULTIPLAYER ==========

@app.post("/tables", response_model=TableInfo)
def api_create_table(table: TableCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = create_table(table.name, current_user, db)
    return TableInfo(
        table_id=obj.id,
        name=obj.name,
        players=[u.username for u in obj.players],
        in_game=obj.in_game,
        winner=obj.winner
    )

@app.post("/tables/join", response_model=TableInfo)
def api_join_table(join: TableJoin, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = join_table(join.table_id, current_user, db)
    if obj is None:
        raise HTTPException(status_code=404, detail="Table not found or already in game")
    return TableInfo(
        table_id=obj.id,
        name=obj.name,
        players=[u.username for u in obj.players],
        in_game=obj.in_game,
        winner=obj.winner
    )

@app.get("/tables", response_model=list[TableInfo])
def api_list_tables(db: Session = Depends(get_db)):
    all_tables = list_tables(db)
    return [
        TableInfo(
            table_id=t.id,
            name=t.name,
            players=[u.username for u in t.players],
            in_game=t.in_game,
            winner=t.winner
        )
        for t in all_tables
    ]

@app.post("/tables/start", response_model=TableInfo)
def api_start_table(table_id: int, db: Session = Depends(get_db)):
    obj = start_table(table_id, db)
    if obj is None:
        raise HTTPException(status_code=404, detail="Table not found or already started")
    return TableInfo(
        table_id=obj.id,
        name=obj.name,
        players=[u.username for u in obj.players],
        in_game=obj.in_game,
        winner=obj.winner
    )

@app.post("/tables/winner", response_model=TableInfo)
def api_table_winner(winner: TableWinner, db: Session = Depends(get_db)):
    obj = declare_winner(winner.table_id, winner.winner, db)
    if obj is None:
        raise HTTPException(status_code=404, detail="Table not found or not in game")
    return TableInfo(
        table_id=obj.id,
        name=obj.name,
        players=[u.username for u in obj.players],
        in_game=obj.in_game,
        winner=obj.winner
    )

# ========== TORNEI ==========

@app.post("/tournaments", response_model=TournamentInfo)
def api_create_tournament(tournament: TournamentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = create_tournament(tournament.name, current_user, db)
    return TournamentInfo(
        tournament_id=obj.id,
        name=obj.name,
        round=obj.round,
        players=[u.username for u in obj.players],
        eliminated=obj.eliminated.split(",") if obj.eliminated else [],
        winner=obj.winner
    )

@app.post("/tournaments/join", response_model=TournamentInfo)
def api_join_tournament(join: TournamentJoin, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    obj = join_tournament(join.tournament_id, current_user, db)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tournament not found or already finished")
    return TournamentInfo(
        tournament_id=obj.id,
        name=obj.name,
        round=obj.round,
        players=[u.username for u in obj.players],
        eliminated=obj.eliminated.split(",") if obj.eliminated else [],
        winner=obj.winner
    )

@app.get("/tournaments", response_model=list[TournamentInfo])
def api_list_tournaments(db: Session = Depends(get_db)):
    all_tournaments = list_tournaments(db)
    return [
        TournamentInfo(
            tournament_id=t.id,
            name=t.name,
            round=t.round,
            players=[u.username for u in t.players],
            eliminated=t.eliminated.split(",") if t.eliminated else [],
            winner=t.winner
        )
        for t in all_tournaments
    ]

@app.post("/tournaments/next_round", response_model=TournamentInfo)
def api_next_round(tournament_id: int, db: Session = Depends(get_db)):
    obj = next_round(tournament_id, db)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tournament not found or already finished")
    return TournamentInfo(
        tournament_id=obj.id,
        name=obj.name,
        round=obj.round,
        players=[u.username for u in obj.players],
        eliminated=obj.eliminated.split(",") if obj.eliminated else [],
        winner=obj.winner
    )

@app.post("/tournaments/winner", response_model=TournamentInfo)
def api_tournament_winner(winner: TournamentWinner, db: Session = Depends(get_db)):
    obj = declare_tournament_winner(winner.tournament_id, winner.winner, db)
    if obj is None:
        raise HTTPException(status_code=404, detail="Tournament not found or already finished")
    return TournamentInfo(
        tournament_id=obj.id,
        name=obj.name,
        round=obj.round,
        players=[u.username for u in obj.players],
        eliminated=obj.eliminated.split(",") if obj.eliminated else [],
        winner=obj.winner
    )
