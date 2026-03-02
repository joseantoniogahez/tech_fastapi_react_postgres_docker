from app.services.password_service import Argon2PasswordService


def test_hash_and_verify_password_round_trip() -> None:
    password_service = Argon2PasswordService()

    hashed_password = password_service.hash_password("StrongPass1")

    assert hashed_password != "StrongPass1"
    assert password_service.verify_password("StrongPass1", hashed_password) is True


def test_verify_password_returns_false_for_invalid_hash() -> None:
    password_service = Argon2PasswordService()

    assert password_service.verify_password("StrongPass1", "not-a-valid-hash") is False
