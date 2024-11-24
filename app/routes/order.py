from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from app.models import User, Order, Pair, UserLot
from app.database import SessionLocal
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/order")
def create_order(pair_id: str, quantity: float, price: float, type: str, x_user_key: str = Header(None), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.key == x_user_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user key")
    
    # Проверяем достаточность баланса
    if type == "buy":
        pair = db.query(Pair).filter(Pair.pair_id == pair_id).first()
        required_balance = price * quantity
        user_lot = db.query(UserLot).filter(UserLot.user_id == user.user_id, UserLot.lot_id == pair.second_lot_id).first()
        if not user_lot or user_lot.quantity < required_balance:
            raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Добавляем ордер
    order = Order(
        order_id=str(uuid.uuid4()),
        user_id=user.user_id,
        pair_id=pair_id,
        quantity=quantity,
        price=price,
        type=type,
        closed=""
    )
    db.add(order)
    db.commit()
    return {"order_id": order.order_id}
