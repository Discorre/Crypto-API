import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Чтение конфигурации
with open('app/config.json') as f:
    config = json.load(f)

DATABASE_URL = f"postgresql://{config['database_user']}:{config['database_password']}@" \
               f"{config['database_ip']}:{config['database_port']}/{config['database_name']}"

# Подключение к БД
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
