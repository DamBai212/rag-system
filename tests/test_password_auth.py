from app.password_auth import hash_password, verify_password


def test_password_hash_round_trip():
    password_hash = hash_password("strong-password", salt_hex="00112233445566778899aabbccddeeff")

    assert verify_password("strong-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_verify_password_rejects_invalid_hash():
    assert verify_password("secret", "not-a-valid-hash") is False
