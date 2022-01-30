from cryptography.fernet import Fernet


def generate_encryption_key(save_path: str) -> bytes:
    key = Fernet.generate_key()
    with open(save_path, 'wb') as f:
        f.write(key)
    return key


def encrypt(key: bytes, id: int) -> bytes:
    f = Fernet(key)
    return f.encrypt(id.to_bytes(id.bit_length(), 'big'))


def decrypt(key: bytes, encrypted_id: bytes) -> int:
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_id)
    return int.from_bytes(decrypted, 'big')
