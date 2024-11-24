from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uuid
from typing import List, Optional

app = FastAPI()

# Хранилище пользователей, их балансов и ордеров (имитация базы данных)
users = {
    "user1": {"key": "a65936b3-6bf6-4819-9b7a-448e7e4c5dad", "balance": {"RUB": 1000, "USD": 1000, "BTC": 10}},
    "user2": {"key": "b2f8e7d3-4d5a-485d-b9b3-5988a83d1b0f", "balance": {"RUB": 1000, "USD": 1000, "BTC": 10}},
}
balances = {}
orders = {}
lot_pairs = {
    1: {"first_lot": "RUB", "second_lot": "USD", "name": "RUB to USD"},
    2: {"first_lot": "RUB", "second_lot": "BTC", "name": "RUB to USD"},
    3: {"first_lot": "USD", "second_lot": "BTC", "name": "USD to BTC"},
    3: {"first_lot": "ETH", "second_lot": "USD", "name": "Ethereum to USD"},
}
lot_names = ["RUB", "USD", "BTC", "ETH"]

# Модели запросов и ответов

class UserRequest(BaseModel):
    username: str

class UserResponse(BaseModel):
    key: str

class BalanceResponse(BaseModel):
    balance: dict

class OrderRequest(BaseModel):
    pair_id: int
    quantity: float
    price: float
    type: str  # "buy" or "sell"

class OrderResponse(BaseModel):
    order_id: str

class Order(BaseModel):
    order_id: str
    user_id: str
    pair_id: int
    quantity: float
    price: float
    type: str  # "buy" or "sell"
    closed: Optional[str] = None

# Создание пользователя
@app.post("/user", response_model=UserResponse)
def create_user(user: UserRequest):
    user_id = str(uuid.uuid4())
    # Генерация ключа пользователя
    key = str(uuid.uuid4())
    users[user_id] = {"username": user.username, "key": key}
    
    # Инициализация баланса: по 1000 единиц каждого актива
    balances[user_id] = {lot: 1000 for lot in lot_names}
    
    return {"key": key}

@app.get("/lot_pairs")
def get_lot_pairs():
    # Возвращаем информацию о всех доступных парах
    return {"lot_pairs": lot_pairs}

@app.get("/lot_pairs/{pair_id}")
def get_lot_pair(pair_id: int):
    # Получаем информацию о конкретной паре
    if pair_id not in lot_pairs:
        raise HTTPException(status_code=404, detail="Pair not found")
    return {"pair_id": pair_id, "info": lot_pairs[pair_id]}

# Получение баланса пользователя
@app.get("/balance", response_model=BalanceResponse)
def get_balance(x_user_key: str = Header(...)):
    user = None
    for username, data in users.items():
        if data["key"] == x_user_key:
            user = username
            break
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"balance": balances[user]}

# Создание ордера
@app.post("/order")
def create_order(order: OrderRequest, x_user_key: str = Header(...)):
    # Найдем пользователя по ключу
    user = None
    for username, data in users.items():
        if data["key"] == x_user_key:
            user = username
            break
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка на существование пары
    if order.pair_id not in lot_pairs:
        raise HTTPException(status_code=400, detail="Invalid pair_id")
    
    # Проверим достаточно ли средств на балансе пользователя
    if order.type == "buy":
        buy_currency = lot_pairs[order.pair_id]["first_lot"]
        total_cost = order.quantity * order.price
        if users[user]["balance"].get(buy_currency, 0) < total_cost:
            raise HTTPException(status_code=400, detail=f"Insufficient funds for purchase. Required: {total_cost}, Available: {users[user]['balance'].get(buy_currency, 0)}")
    elif order.type == "sell":
        sell_currency = lot_pairs[order.pair_id]["first_lot"]
        if users[user]["balance"].get(sell_currency, 0) < order.quantity:
            raise HTTPException(status_code=400, detail="Insufficient assets to sell")
    
    # Генерация уникального ID для ордера
    order_id = str(uuid.uuid4())
    
    # Сохраняем ордер
    orders[order_id] = {
        "order_id": order_id,
        "user_id": user,
        "pair_id": order.pair_id,
        "quantity": order.quantity,
        "price": order.price,
        "type": order.type,
        "closed": None,
    }
    
    # Если ордер на покупку, обновляем баланс покупателя
    if order.type == "buy":
        buy_currency = lot_pairs[order.pair_id]["first_lot"]
        users[user]["balance"][buy_currency] -= order.quantity * order.price
    # Если ордер на продажу, обновляем баланс продавца
    elif order.type == "sell":
        sell_currency = lot_pairs[order.pair_id]["first_lot"]
        users[user]["balance"][sell_currency] -= order.quantity
    
    # Проверка на совпадение ордеров с другим пользователем
    for existing_order_id, existing_order in orders.items():
        # Игнорируем ордера одного пользователя
        if existing_order["user_id"] == user or existing_order["closed"] == "done":
            continue
        
        if existing_order["type"] == "buy" and existing_order["pair_id"] == order.pair_id and existing_order["price"] >= order.price:
            # Сделка завершена (покупка)
            trade_quantity = min(order.quantity, existing_order["quantity"])
            trade_amount = trade_quantity * order.price

            users[existing_order["user_id"]]["balance"][lot_pairs[order.pair_id]["first_lot"]] += trade_quantity
            users[user]["balance"][lot_pairs[order.pair_id]["first_lot"]] -= trade_quantity
            users[existing_order["user_id"]]["balance"][lot_pairs[order.pair_id]["second_lot"]] -= trade_amount
            users[user]["balance"][lot_pairs[order.pair_id]["second_lot"]] += trade_amount
            
            # Обновляем ордера
            orders[existing_order_id]["quantity"] -= trade_quantity
            orders[order_id]["quantity"] -= trade_quantity
            
            if orders[existing_order_id]["quantity"] == 0:
                orders[existing_order_id]["closed"] = "done"
            if orders[order_id]["quantity"] == 0:
                orders[order_id]["closed"] = "done"
            
            return {"order_id": order_id, "message": "Order completed", "trade_quantity": trade_quantity}

        if existing_order["type"] == "sell" and existing_order["pair_id"] == order.pair_id and existing_order["price"] <= order.price:
            # Сделка завершена (продажа)
            trade_quantity = min(order.quantity, existing_order["quantity"])
            trade_amount = trade_quantity * existing_order["price"]

            users[existing_order["user_id"]]["balance"][lot_pairs[order.pair_id]["first_lot"]] += trade_quantity
            users[user]["balance"][lot_pairs[order.pair_id]["first_lot"]] -= trade_quantity
            users[existing_order["user_id"]]["balance"][lot_pairs[order.pair_id]["second_lot"]] -= trade_amount
            users[user]["balance"][lot_pairs[order.pair_id]["second_lot"]] += trade_amount
            
            # Обновляем ордера
            orders[existing_order_id]["quantity"] -= trade_quantity
            orders[order_id]["quantity"] -= trade_quantity
            
            if orders[existing_order_id]["quantity"] == 0:
                orders[existing_order_id]["closed"] = "done"
            if orders[order_id]["quantity"] == 0:
                orders[order_id]["closed"] = "done"
            
            return {"order_id": order_id, "message": "Order completed", "trade_quantity": trade_quantity}

    return {"order_id": order_id, "message": "Order placed"}

# Получение баланса пользователя
@app.get("/order", response_model=List[Order])
def get_orders():
    if not orders:
        raise HTTPException(status_code=404, detail="No orders found")
    
    return list(orders.values())

# Удаление ордера
@app.delete("/order/{order_id}")
def delete_order(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    del orders[order_id]  # Удаляем ордер по его ID
    return {"message": "Order deleted successfully", "order_id": order_id}
