import secrets

def generate_token(length=32) -> str:
    return secrets.token_urlsafe(length)