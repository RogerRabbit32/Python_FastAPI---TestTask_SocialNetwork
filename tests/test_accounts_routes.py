import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.mark.parametrize(
    "username, email, password, expected_status_code, expected_message",
    [
        ("GuildNavigator", "levinkirill@yandex.ru", "password1", 200, None),  # Successful registration
        ("GuildNavigator", "test@example.com", "password1", 400, "Login already exists"),  # Duplicate username
        ("GuildNavigator2", "levinkirill@yandex.ru", "password1", 400, "Email already exists"),  # Duplicate email
        ("", "", "", 422, None),  # All empty values
        ("", "test@example.com", "password1", 422, None),  # Empty username
        ("GuildNavigator2", "", "password1", 422, None),  # Empty email
        ("GuildNavigator2", "test@example.com", "", 422, None),  # Empty password
        ("Gui", "test@example.com", "password1", 422, None),  # Username too short
        ("GuildNavigator2", "test@example.com", "password", 422, None),  # Password too simple
        ("GuildNavigator2", "invalid@invalid.com", "password1", 400,
         "Email existence verification failed. Please provide a valid email"),  # Invalid email
    ]
)
def test_user_registration(username, email, password, expected_status_code, expected_message):
    response = client.post(
        "/accounts/signup", json={
                "username": username,
                "email": email,
                "password": password
        }
    )
    assert response.status_code == expected_status_code
    if expected_message:
        assert expected_message in response.text


@pytest.mark.parametrize(
    "username, password, expected_status_code, expected_result",
    [
        ("GuildNavigator", "password1", 200, True),  # Existing user with valid password
        ("GuildNavigator", "wrong-password1", 401, False),  # Existing user with invalid password
        ("Lisan Al-Gaib", "password1", 401, False)  # Non-existing user
    ]
)
def test_user_login(username, password, expected_status_code, expected_result):
    response = client.post(
        "/accounts/login", data={
                "username": username,
                "password": password
        }
    )
    assert response.status_code == expected_status_code
    response_json = response.json()
    if expected_result is True:
        assert "access_token" in response_json
        assert response_json["token_type"] == "bearer"
