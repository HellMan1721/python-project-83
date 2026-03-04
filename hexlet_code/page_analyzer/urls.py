import psycopg
from urllib.parse import urlparse
import validators
import os
from dotenv import load_dotenv

load_dotenv()

class URL:
    @staticmethod
    def get_connection():
        return psycopg.connect(os.getenv('DATABASE_URL'))
    
    @staticmethod
    def normalize(url):
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc.lower()}"
    
    @staticmethod
    def save(url):
        normalized = URL.normalize(url)
        if not validators.url(normalized) or len(normalized) > 255:
            raise ValueError("Некорректный URL")
        
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id",
                    (normalized,)
                )
                result = cur.fetchone()
                if not result:
                    # Уже существует
                    cur.execute("SELECT id FROM urls WHERE name = %s", (normalized,))
                    return cur.fetchone()[0]
                return result[0]
    
    @staticmethod
    def all():
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls ORDER BY created_at DESC")
                return cur.fetchall()
    
    @staticmethod
    def get(id):
        with URL.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
                return cur.fetchone()
