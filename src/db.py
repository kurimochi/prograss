import os
import psycopg2
import time


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
            break
        except psycopg2.OperationalError:
            print(f"DB connection failed, retry... ({i+1}/10)")
            time.sleep(3)
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
    for t in TABLES:
        cursor.execute(t)
    conn.commit()

    return conn, cursor


def registered(user_id, cursor):
    cursor.execute("SELECT 1 FROM users WHERE user_id = %s LIMIT 1", (user_id,))
    return cursor.fetchone() is not None


def aggr_internal(user_id, cursor):
    cursor.execute("SELECT message FROM progress WHERE user_id = %s", (user_id,))
    return [row[0] for row in cursor.fetchall()]
