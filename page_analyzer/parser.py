import requests
from bs4 import BeautifulSoup
from .urls import URL
from .database import get_connection


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

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO url_checks (
                    url_id, status_code, h1, title, description
                    ) 
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
