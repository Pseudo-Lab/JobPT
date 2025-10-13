# loader.py
import getpass
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import sys

def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return kdf.derive(passphrase.encode())

def run_encrypted(path: str, passphrase: str):
    with open(path, 'rb') as f:
        raw = f.read()
    if len(raw) < 28:
        raise ValueError("Encrypted file too small/invalid")
    salt = raw[:16]
    nonce = raw[16:28]
    ct = raw[28:]
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ct, None)
    except Exception as e:
        raise ValueError("복호화 실패: 잘못된 키일 수 있습니다.") from e
    code = plaintext.decode('utf-8', errors='replace')
    compiled = compile(code, "<decrypted>", "exec")
    exec(compiled, {"__name__": "__main__"})

if __name__ == "__main__":
    enc_path = "git_agent_token_base.enc"
    passphrase = "1234"
    try:
        run_encrypted(enc_path, passphrase)
    except Exception as e:
        print("오류:", e)
        sys.exit(1)
