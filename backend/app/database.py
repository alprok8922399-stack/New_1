import databases
import sqlalchemy
import os

# ⚠️⚠️⚠️ ОБЯЗАТЕЛЬНО ЗАПОЛНИТЕ ЭТИ ДАННЫЕ ⚠️⚠️⚠️
DB_USER = os.getenv("POSTGRES_USER", "")  
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")  
DB_HOST = os.getenv("POSTGRES_SERVER", "")  
DB_PORT = os.getenv("POSTGRES_PORT", "")  
DB_NAME = os.getenv("POSTGRES_DB", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Таблица сообщений
messages = sqlalchemy.Table(
    "messages",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("role", sqlalchemy.String),
    sqlalchemy.Column("content", sqlalchemy.Text),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime)
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)
