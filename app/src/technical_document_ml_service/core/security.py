from __future__ import annotations

import hashlib
import secrets


def hash_password(raw_password: str) -> str:
    """
    получить SHA-256 хэш пароля
    """
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


def verify_password(raw_password: str, password_hash: str) -> bool:
    """проверить соответствие пароля его хэшу"""
    candidate_hash = hash_password(raw_password)
    return secrets.compare_digest(candidate_hash, password_hash)