from sqlalchemy import create_engine, Column, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    key = Column(String, nullable=False)

class Lot(Base):
    __tablename__ = 'lot'
    lot_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)

class UserLot(Base):
    __tablename__ = 'user_lot'
    user_id = Column(String, ForeignKey('user.user_id'), primary_key=True)
    lot_id = Column(String, ForeignKey('lot.lot_id'), primary_key=True)
    quantity = Column(Float, nullable=False)

class Pair(Base):
    __tablename__ = 'pair'
    pair_id = Column(String, primary_key=True)
    first_lot_id = Column(String, ForeignKey('lot.lot_id'))
    second_lot_id = Column(String, ForeignKey('lot.lot_id'))

class Order(Base):
    __tablename__ = 'order'
    order_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('user.user_id'))
    pair_id = Column(String, ForeignKey('pair.pair_id'))
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    closed = Column(String, nullable=True)
