from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import User, UserLot, Lot
from app.database import SessionLocal
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/user")
def create_user(username: str, db: Session = Depends(get_db)):
    user_id = str(uuid.uuid4())
    key = uuid.uuid4().hex
    
    # Создаем пользователя
    user = User(user_id=user_id, username=username, key=key)
    db.add(user)
    
    # Создаем начальный баланс
    lots = db.query(Lot).all()
    for lot in lots:
        db.add(UserLot(user_id=user_id, lot_id=lot.lot_id, quantity=1000.0))
    
    db.commit()
    return {"key": key}
