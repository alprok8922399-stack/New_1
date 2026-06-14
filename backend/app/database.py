import databases
import sqlalchemy
import os

# Настройки БД
DB_USER = os.getenv("POSTGRES_USER", "")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_SERVER", "")
DB_PORT = os.getenv("POSTGRES_PORT", "")
DB_NAME = os.getenv("POSTGRES_DB", "")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Новая таблица USERS
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime)
)

# Таблица MESSAGES (связываем с пользователями)
messages = sqlalchemy.Table(
    "messages",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("role", sqlalchemy.String),
    sqlalchemy.Column("content", sqlalchemy.Text),
    sqlalchemy.Column("timestamp", sqlalchemy.DateTime)
)

# Создание таблиц
engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)
