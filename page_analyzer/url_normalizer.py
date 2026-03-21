from urllib.parse import urlparse


def normalize(url):
    if not url.startswith("http"):
        url = f"https://{url}"

    parsed = urlparse(url.lower())
    return f"{parsed.scheme}://{parsed.netloc}/"


def validate(url: str) -> bool:
    """Базовая валидация URL."""
    normalized = normalize(url)
    return len(normalized) <= 255 and normalized.startswith(
        ("http://", "https://")
    )
