from cryptography.fernet import Fernet, InvalidToken


def encrypt_invitation_token(raw_token: str, encryption_key: str) -> bytes:
    return Fernet(encryption_key.encode()).encrypt(raw_token.encode())


def decrypt_invitation_token(
    token_ciphertext: bytes, encryption_key: str
) -> str | None:
    try:
        return Fernet(encryption_key.encode()).decrypt(token_ciphertext).decode()
    except InvalidToken:
        return None
