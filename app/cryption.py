import os

from bson.binary import Binary
from bson.codec_options import CodecOptions
from config import (
    MASTER_KEY_PATH,
    NAME_OF_COLLECTION_CRYPTO,
    NAME_OF_DATABASE_CRYPTO,
    URI_CRYPTO,
)
from pymongo import MongoClient
from pymongo.encryption import ClientEncryption


def load_or_generate_master_key():
    if os.path.exists(MASTER_KEY_PATH):
        with open(MASTER_KEY_PATH, "rb") as f:
            return f.read()
    else:
        key = os.urandom(96)
        with open(MASTER_KEY_PATH, "wb") as f:
            f.write(key)
        return key


client_shifr = MongoClient(URI_CRYPTO)
key_vault_db = client_shifr[NAME_OF_DATABASE_CRYPTO]
key_vault_collection = key_vault_db[NAME_OF_COLLECTION_CRYPTO]

local_master_key = load_or_generate_master_key()
kms_providers = {"local": {"key": local_master_key}}

client_encryption = ClientEncryption(
    kms_providers,
    f"{NAME_OF_DATABASE_CRYPTO}.{NAME_OF_COLLECTION_CRYPTO}",
    client_shifr,
    codec_options=CodecOptions(),
)

existing_key = key_vault_collection.find_one({})
if existing_key:
    key_id = existing_key["_id"]
else:
    key_id = client_encryption.create_data_key("local")


def encrypt_text(text: str) -> Binary:
    encrypted = client_encryption.encrypt(
        text, algorithm="AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic", key_id=key_id
    )
    return Binary(encrypted, subtype=6)


def decrypt_text(encrypted_text: Binary) -> str:
    return client_encryption.decrypt(encrypted_text)
