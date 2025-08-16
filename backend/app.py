from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db, init_db
from schemas import (
    UserCreate, UserOut, Token, TableCreate, TableInfo, TableJoin,
    TableWinner, TournamentCreate, TournamentInfo, TournamentJoin,
    TournamentWinner, PaymentResponse
)
from crud import (
    create_user, get_user, create_table, join_table,
    start_table, declare_table_winner, create_tournament,
    join_tournament, next_tournament_round, declare_tournament_winner,
    update_user_balance, record_transaction
)
from security import create_access_token, verify_password, decode_token
from coinbase import send_usdc, verify_coinbase_payment
import os
from datetime import timedelta
from models import User

app = FastAPI()

# Inizializza DB al primo avvio
@app.on_event("startup")
def on_startup():
    init_db()

# Endpoint di autenticazione
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Registrazione utente con pagamento fee
@app.post("/register", response_model=PaymentResponse)
async def register_user(
    user: UserCreate, 
    user_wallet: str,  # Wallet USDC dell'utente
    db: Session = Depends(get_db)
):
    REGISTRATION_FEE = float(os.getenv("REGISTRATION_FEE", "20.0"))
    
    # Verifica se l'utente esiste già
    if get_user(db, user.username):
        raise HTTPException(
            status_code=400,
            detail="Username già registrato"
        )
    
    # Effettua il pagamento a Coinbase
    success, message, tx_hash = send_usdc(REGISTRATION_FEE, user_wallet)
    
    if success:
        # Crea l'utente dopo il pagamento confermato
        db_user = create_user(db, {
            "username": user.username,
            "password": user.password
        })
        
        # Registra la transazione
        record_transaction(
            db, 
            db_user.id, 
            -REGISTRATION_FEE, 
            "registration_fee",
            tx_hash
        )
        
        return {
            "status": True,
            "message": "Registrazione completata",
            "tx_hash": tx_hash
        }
    else:
        return {
            "status": False,
            "message": f"Pagamento fallito: {message}"
        }

# Endpoint per il gioco
@app.post("/tables/create", response_model=TableInfo)
async def create_game_table(
    table: TableCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    username = decode_token(token).get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    return create_table(db, table.name, user)

@app.post("/tables/join", response_model=TableInfo)
async def join_game_table(
    table_join: TableJoin,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    username = decode_token(token).get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    join_table(db, table_join.table_id, user.id)
    table = db.query(Table).filter(Table.id == table_join.table_id).first()
    return table

@app.post("/tables/start", response_model=TableInfo)
async def start_game_table(
    table_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    username = decode_token(token).get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    return start_table(db, table_id)

@app.post("/tables/declare_winner", response_model=TableInfo)
async def declare_table_winner_endpoint(
    winner: TableWinner,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    username = decode_token(token).get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    return declare_table_winner(db, winner.table_id, winner.winner)

# Endpoint per tornei (simili ai tavoli)

# Endpoint per prelievo fondi
@app.post("/withdraw", response_model=PaymentResponse)
async def withdraw_funds(
    amount: float,
    user_wallet: str,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    username = decode_token(token).get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    
    if user.usdc_balance < amount:
        raise HTTPException(
            status_code=400,
            detail="Saldo insufficiente"
        )
    
    # Invia USDC all'utente
    success, message, tx_hash = send_usdc(amount, user_wallet)
    
    if success:
        # Aggiorna saldo utente
        user.usdc_balance -= amount
        db.commit()
        
        # Registra transazione
        record_transaction(
            db, 
            user.id, 
            -amount, 
            "withdraw",
            tx_hash
        )
        
        return {
            "status": True,
            "message": "Prelievo effettuato",
            "tx_hash": tx_hash
        }
    else:
        return {
            "status": False,
            "message": f"Prelievo fallito: {message}"
        }

# Endpoint utente
@app.get("/me", response_model=UserOut)
async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    username = decode_token(token).get("sub")
    user = get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    return user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
