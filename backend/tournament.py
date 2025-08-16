from database import SessionLocal, Tournament, User
from sqlalchemy.orm import Session
import os
import random

TOURNAMENT_FEE = float(os.getenv("TOURNAMENT_FEE", "1"))

def create_tournament(name: str, creator: User, db: Session):
    tournament = Tournament(name=name, round=1, winner=None, eliminated="")
    tournament.players.append(creator)
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament

def join_tournament(tournament_id: int, user: User, db: Session):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament and not tournament.winner and user not in tournament.players:
        tournament.players.append(user)
        db.commit()
    return tournament

def next_round(tournament_id: int, db: Session):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament and not tournament.winner:
        eliminated = tournament.eliminated.split(",") if tournament.eliminated else []
        remaining = [u.username for u in tournament.players if u.username not in eliminated]
        if len(remaining) == 1:
            tournament.winner = remaining[0]
            tournament.round += 1
            db.commit()
            return tournament
        to_eliminate = random.sample(remaining, max(1, len(remaining)//2))
        eliminated += to_eliminate
        tournament.eliminated = ",".join(eliminated)
        tournament.round += 1
        db.commit()
        return tournament

def declare_tournament_winner(tournament_id: int, winner_username: str, db: Session):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if tournament and not tournament.winner:
        tournament.winner = winner_username
        db.commit()
        user = db.query(User).filter(User.username == winner_username).first()
        if user:
            user.tournaments_won += 1
            user.usdc_balance += TOURNAMENT_FEE * len(tournament.players)
            db.commit()
    return tournament

def list_tournaments(db: Session):
    return db.query(Tournament).all()
