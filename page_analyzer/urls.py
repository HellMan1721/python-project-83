import psycopg
import validators
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


class DuplicateUrlError(Exception):
    """URL уже существует."""

    pass


class ValidationError(Exception):
    """Некорректный URL."""

    pass


class URL:
    @staticmethod
    def init_db():
        """Создание таблиц (игнорируем дубликаты)."""
        try:
            with URL.get_connection() as conn:
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

    @staticmethod
    def get_connection():
        return psycopg.connect(os.getenv("DATABASE_URL"))

    @staticmethod
    def normalize(url):
        if not url.startswith("http"):
            url = f"https://{url}"

        parsed = urlparse(url.lower())
        return f"{parsed.scheme}://{parsed.netloc}/"

    @staticmethod
    def save(url):
        normalized = URL.normalize(url)

        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM urls WHERE name = %s", (normalized,))
                existing = cur.fetchone()
                if existing:
                    raise DuplicateUrlError(existing[0])

                if not validators.url(url) or len(normalized) > 255:
                    raise ValidationError("Некорректный URL")

                cur.execute(
                    "INSERT INTO urls (name) VALUES (%s) RETURNING id", (normalized,)
                )
                url_id = cur.fetchone()[0]
                conn.commit()
                return url_id

    @staticmethod
    def all():
        """Все URL + дата И КОД последней проверки"""
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        u.id, 
                        u.name, 
                        u.created_at,
                        c.status_code as last_status
                        c.created_at as last_check,
                    FROM urls u 
                    LEFT JOIN (
                        SELECT url_id, 
                            created_at, 
                            status_code,
                            ROW_NUMBER() OVER (PARTITION BY url_id ORDER BY created_at DESC) as rn
                        FROM url_checks
                    ) c ON u.id = c.url_id AND c.rn = 1
                    ORDER BY u.created_at DESC
                """)
                return cur.fetchall()

    @staticmethod
    def get(id):
        """Один URL по ID"""
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
                return cur.fetchone()

    @staticmethod
    def get_checks(url_id):
        """Все проверки для сайта"""
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC",
                    (url_id,),
                )
                return cur.fetchall()

    @staticmethod
    def create_check(url_id):
        """Полная проверка: status_code + h1 + title + description"""
        url_data = URL.get(url_id)
        if not url_data:
            raise Exception("URL not found")

        url_name = url_data[1]

        try:
            response = requests.get(url_name, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            h1 = soup.find("h1")
            h1_text = h1.get_text(strip=True) if h1 else None

            title = soup.find("title")
            title_text = title.get_text(strip=True) if title else None

            description = soup.find("meta", attrs={"name": "description"})
            description_text = (
                description.get("content", "").strip() if description else None
            )

            with URL.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO url_checks (url_id, status_code, h1, title, description) 
                        VALUES (%s, %s, %s, %s, %s) RETURNING id
                    """,
                        (
                            url_id,
                            response.status_code,
                            h1_text,
                            title_text,
                            description_text,
                        ),
                    )
                    check_id = cur.fetchone()[0]
                    conn.commit()
                    return check_id

        except (requests.RequestException, requests.exceptions.HTTPError):
            raise Exception("Request failed")


URL.init_db()
