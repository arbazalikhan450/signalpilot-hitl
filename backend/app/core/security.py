import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet


def _build_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class TokenCipher:
    def __init__(self, secret: str) -> None:
        self._fernet = Fernet(_build_fernet_key(secret))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
