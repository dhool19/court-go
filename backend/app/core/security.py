import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from pwdlib import PasswordHash

load_dotenv()

secret_key = os.environ["JWT_SECRET_KEY"]
algorithm = "HS256"

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)
