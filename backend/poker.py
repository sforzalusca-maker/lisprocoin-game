from database import SessionLocal, Table, User
from sqlalchemy.orm import Session
import os

GAME_FEE = float(os.getenv("GAME_FEE", "0.03"))

def create_table(name: str, creator: User, db: Session):
    table = Table(name=name, in_game=False, winner=None)
    table.players.append(creator)
    db.add(table)
    db.commit()
    db.refresh(table)
    return table

def join_table(table_id: int, user: User, db: Session):
    table = db.query(Table).filter(Table.id == table_id).first()
    if table and not table.in_game and user not in table.players:
        table.players.append(user)
        db.commit()
    return table

def start_table(table_id: int, db: Session):
    table = db.query(Table).filter(Table.id == table_id).first()
    if table and not table.in_game:
        table.in_game = True
        db.commit()
    return table

def declare_winner(table_id: int, winner_username: str, db: Session):
    table = db.query(Table).filter(Table.id == table_id).first()
    if table and table.in_game:
        table.winner = winner_username
        table.in_game = False
        db.commit()
        user = db.query(User).filter(User.username == winner_username).first()
        if user:
            user.games_won += 1
            user.usdc_balance += GAME_FEE * len(table.players)
            db.commit()
    return table

def list_tables(db: Session):
    return db.query(Table).all()
