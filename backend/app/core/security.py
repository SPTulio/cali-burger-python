"""Senhas (bcrypt) e tokens de sessão."""

import hashlib
import hmac
import secrets

import bcrypt

from app.core.config import get_settings

# Hash válido usado quando o usuário não existe, para que o tempo de resposta do
# login não revele se a conta existe.
_DUMMY_HASH = bcrypt.hashpw(b"cali-burger-dummy", bcrypt.gensalt(rounds=4))


def hash_password(password: str) -> str:
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=rounds)).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    """Confere a senha. Aceita hashes `$2y$` gerados pelo PHP (sistema legado)."""
    if not password_hash:
        bcrypt.checkpw(password.encode(), _DUMMY_HASH)
        return False
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True se o hash é de outro formato/custo e deve ser regravado no próximo login."""
    if not password_hash.startswith("$2b$"):
        return True
    try:
        cost = int(password_hash.split("$")[2])
    except (IndexError, ValueError):
        return True
    return cost < get_settings().bcrypt_rounds


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_match(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_token(token), expected_hash)
