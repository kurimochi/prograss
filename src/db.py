import os
import psycopg2
import time
from logging import getLogger, StreamHandler, Formatter, INFO

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(INFO)
logger.propagate = False


def init_db():
    DB_NAME = os.getenv("POSTGRES_DB")
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASS = os.getenv("POSTGRES_PASSWORD")

    # DB初期化
    for i in range(10):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME, user=DB_USER, password=DB_PASS, host="db"
            )
            logger.info("Successfully connected to PostgreSQL.")
            break
        except psycopg2.OperationalError as e:
            print(f"DB connection failed, retry... ({i+1}/10)")
            time.sleep(3)
            logger.exception(f"PostgreSQL connection error: {e}")
    else:
        raise Exception("Could not connect to PostgreSQL.")

    cursor = conn.cursor()

    # テーブル作成
    TABLES = [
        """CREATE TABLE IF NOT EXISTS progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            notice TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS channels (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            channel BIGINT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS votes (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message_id BIGINT NOT NULL,
            consent INTEGER NOT NULL,
            refusal INTEGER NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS backup_progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    try:
        for t in TABLES:
            cursor.execute(t)
            logger.info(f"Table created or already exists: {t}")
        conn.commit()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.exception(f"Error creating tables: {e}")
        conn.rollback()
        raise

    return conn, cursor


def registered(user_id, cursor):
    try:
        cursor.execute("SELECT 1 FROM users WHERE user_id = %s LIMIT 1", (user_id,))
        result = cursor.fetchone()
        logger.info(f"Checking if user {user_id} is registered.")
        return result is not None
    except Exception as e:
        logger.exception(f"Error checking registration for user {user_id}: {e}")
        raise


def aggr_internal(user_id, cursor):
    try:
        cursor.execute("SELECT message FROM progress WHERE user_id = %s", (user_id,))
        messages = [row[0] for row in cursor.fetchall()]
        logger.info(f"Retrieved messages for user {user_id}.")
        return messages
    except Exception as e:
        logger.exception(f"Error retrieving messages for user {user_id}: {e}")
        raise
