import psycopg
import os
import validators
from .url_normalizer import normalize


class DuplicateUrlError(Exception):
    """URL уже существует."""

    pass


class ValidationError(Exception):
    """Некорректный URL."""

    pass


def init_db():
    """Создание таблиц (игнорируем дубликаты)."""
    try:
        with get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS url_checks (
                    id SERIAL PRIMARY KEY,
                    url_id INTEGER NOT NULL REFERENCES urls (id),
                    status_code INTEGER,
                    h1 VARCHAR(255),
                    title VARCHAR(255),
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Таблицы уже существуют: {e}")


def get_connection():
    return psycopg.connect(os.getenv("DATABASE_URL"))


def save(url):
    normalized = normalize(url)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (normalized,))
            existing = cur.fetchone()
            if existing:
                raise DuplicateUrlError(existing[0])

            if not validators.url(url) or len(normalized) > 255:
                raise ValidationError("Некорректный URL")

            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (normalized,),
            )
            url_id = cur.fetchone()[0]
            conn.commit()
            return url_id
