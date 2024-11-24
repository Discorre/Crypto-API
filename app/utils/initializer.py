from sqlalchemy.orm import Session
from app.models import Base, engine, Lot, Pair
import json

def initialize_db():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    
    # Загружаем конфигурацию
    with open('app/config.json') as f:
        config = json.load(f)
    
    # Добавляем лоты
    for idx, name in enumerate(config['lots']):
        session.add(Lot(lot_id=str(idx + 1), name=name))
    
    # Создаем пары "каждый с каждым"
    lots = config['lots']
    pair_id = 1
    for i, lot1 in enumerate(lots):
        for lot2 in lots[i + 1:]:
            session.add(Pair(pair_id=str(pair_id), first_lot_id=str(i + 1), second_lot_id=str(i + 2)))
            pair_id += 1
    
    session.commit()
    session.close()
