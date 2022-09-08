from cryptography.fernet import Fernet
from toxic_bot.helpers.database import Database

def generate_encryption_key() -> bytes:
    key = Fernet.generate_key()
    return key


def encrypt(key: bytes, id: int) -> bytes:
    f = Fernet(key)
    return f.encrypt(id.to_bytes(id.bit_length(), 'big'))


def decrypt(key: bytes, encrypted_id: bytes) -> int:
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_id)
    return int.from_bytes(decrypted, 'big')
