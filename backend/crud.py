from sqlalchemy.orm import Session
from models import User, Table, Tournament, TablePlayer, TournamentPlayer, Transaction
from security import get_password_hash
import os
import random
from datetime import datetime

REGISTRATION_FEE = float(os.getenv("REGISTRATION_FEE", "20.0"))
GAME_FEE = float(os.getenv("GAME_FEE", "0.03"))
TOURNAMENT_FEE = float(os.getenv("TOURNAMENT_FEE", "1.0"))

# Operazioni utente
def create_user(db: Session, user: dict):
    hashed_password = get_password_hash(user['password'])
    db_user = User(
        username=user['username'],
        hashed_password=hashed_password,
        usdc_balance=0.0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def update_user_balance(db: Session, username: str, amount: float):
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.usdc_balance += amount
        db.commit()
        return user
    return None

def record_transaction(db: Session, user_id: int, amount: float, tx_type: str, tx_hash: str = None):
    tx = Transaction(
        user_id=user_id,
        amount=amount,
        tx_type=tx_type,
        tx_hash=tx_hash
    )
    db.add(tx)
    db.commit()
    return tx

# Operazioni tavolo
def create_table(db: Session, name: str, creator: User):
    table = Table(name=name)
    db.add(table)
    db.commit()
    db.refresh(table)
    
    # Aggiungi creatore al tavolo
    join_table(db, table.id, creator.id)
    return table

def join_table(db: Session, table_id: int, user_id: int):
    # Verifica se l'utente è già nel tavolo
    existing = db.query(TablePlayer).filter(
        TablePlayer.table_id == table_id,
        TablePlayer.user_id == user_id
    ).first()
    
    if not existing:
        player = TablePlayer(table_id=table_id, user_id=user_id)
        db.add(player)
        db.commit()
        return player
    return existing

def start_table(db: Session, table_id: int):
    table = db.query(Table).filter(Table.id == table_id).first()
    if table and not table.in_game:
        table.in_game = True
        # Addebita la fee di gioco a tutti i giocatori
        players = db.query(TablePlayer).filter(TablePlayer.table_id == table_id).all()
        for player in players:
            user = db.query(User).filter(User.id == player.user_id).first()
            if user:
                user.usdc_balance -= GAME_FEE
                user.games_played += 1
                record_transaction(db, user.id, -GAME_FEE, "game_fee")
        db.commit()
        return table
    return None

def declare_table_winner(db: Session, table_id: int, winner_username: str):
    table = db.query(Table).filter(Table.id == table_id).first()
    if table and table.in_game:
        table.winner = winner_username
        table.in_game = False
        
        # Calcola il premio
        players = db.query(TablePlayer).filter(TablePlayer.table_id == table_id).all()
        prize_pool = len(players) * GAME_FEE
        
        # Assegna il premio al vincitore
        winner = get_user(db, winner_username)
        if winner:
            winner.usdc_balance += prize_pool
            winner.games_won += 1
            record_transaction(db, winner.id, prize_pool, "game_win")
        
        db.commit()
        return table
    return None

# Operazioni torneo
def create_tournament(db: Session, name: str, creator: User):
    tournament = Tournament(name=name)
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    # Aggiungi creatore al torneo
    join_tournament(db, tournament.id, creator.id)
    return tournament

def join_tournament(db: Session, tournament_id: int, user_id: int):
    # Verifica se l'utente è già nel torneo
    existing = db.query(TournamentPlayer).filter(
        TournamentPlayer.tournament_id == tournament_id,
        TournamentPlayer.user_id == user_id
    ).first()
    
    if not existing:
        player = TournamentPlayer(tournament_id=tournament_id, user_id=user_id)
        db.add(player)
        db.commit()
        return player
    return existing

def next_tournament_round(db: Session, tournament_id: int):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament and not tournament.winner:
        # Ottieni tutti i giocatori non eliminati
        players = db.query(TournamentPlayer).filter(
            TournamentPlayer.tournament_id == tournament_id
        ).all()
        
        player_ids = [p.user_id for p in players]
        eliminated = [int(id) for id in tournament.eliminated.split(',')] if tournament.eliminated else []
        active_players = [pid for pid in player_ids if pid not in eliminated]
        
        if len(active_players) <= 1:
            return None  # Torneo finito
        
        # Elimina casualmente metà dei giocatori
        eliminate_count = max(1, len(active_players) // 2)
        to_eliminate = random.sample(active_players, eliminate_count)
        
        # Aggiorna lista eliminati
        new_eliminated = eliminated + to_eliminate
        tournament.eliminated = ','.join(map(str, new_eliminated))
        tournament.round += 1
        db.commit()
        
        return tournament
    return None

def declare_tournament_winner(db: Session, tournament_id: int, winner_username: str):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament and not tournament.winner:
        tournament.winner = winner_username
        
        # Calcola il premio
        players = db.query(TournamentPlayer).filter(
            TournamentPlayer.tournament_id == tournament_id
        ).all()
        prize_pool = len(players) * TOURNAMENT_FEE
        
        # Assegna il premio al vincitore
        winner = get_user(db, winner_username)
        if winner:
            winner.usdc_balance += prize_pool
            winner.tournaments_won += 1
            record_transaction(db, winner.id, prize_pool, "tournament_win")
        
        db.commit()
        return tournament
    return None
