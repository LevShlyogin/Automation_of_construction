import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настройка строки подключения к базе данных
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:Nehbyf66@db:5432/postgres"

# Создаем движок (engine) для подключения к базе данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Создаем класс SessionLocal для создания сессий с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей ORM
Base = sqlalchemy.orm.declarative_base()