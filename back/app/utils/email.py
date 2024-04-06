import requests

from app.config import settings


def verify_email(email: str) -> bool:
    """Verify email using Hunter API.

    Args:
        email (str): Email to verify.

    Returns:
        bool: True if email is valid, False otherwise.
    """
    params = {"email": email, "api_key": settings.HUNTER_API}
    response = requests.get(settings.HUNTER_URI, params=params)
    if response.status_code == 200:
        return response.json()["data"]["status"] == "valid"
    return False
