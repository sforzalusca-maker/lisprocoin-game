from sqlalchemy.orm import Session
from . import models
from .security import get_password_hash
import os
import random

REGISTRATION_FEE = float(os.getenv("REGISTRATION_FEE", "20.0"))
GAME_FEE = float(os.getenv("GAME_FEE", "0.03"))
TOURNAMENT_FEE = float(os.getenv("TOURNAMENT_FEE", "1.0"))

def create_user(db: Session, username: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = models.User(
        username=username,
        hashed_password=hashed_password,
        usdc_balance=0.0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# Altre funzioni CRUD mantenute semplici...
