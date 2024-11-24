from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app import models, database

router = APIRouter()

# Получение всех пар активов
@router.get("/pair", response_model=list[models.Pair])
def get_pairs(db: Session = Depends(database.get_db)):
    return db.query(models.Pair).all()

# Получение информации о конкретной паре
@router.get("/pair/{pair_id}", response_model=models.Pair)
def get_pair(pair_id: int, db: Session = Depends(database.get_db)):
    pair = db.query(models.Pair).filter(models.Pair.id == pair_id).first()
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    return pair
