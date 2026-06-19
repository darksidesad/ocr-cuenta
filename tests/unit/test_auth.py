"""Tests unitarios para autenticación JWT."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import authenticate_user, create_access_token, verify_token

SECRET = "test-secret-key-for-jwt-minimum-32-bytes!!"


class TestCreateAccessToken:
    """Tests para create_access_token."""

    @patch("app.auth.settings")
    def test_crea_token_valido(self, mock_settings):
        mock_settings.jwt_secret_key = SECRET
        mock_settings.jwt_expire_minutes = 60

        token = create_access_token("admin")
        assert isinstance(token, str)
        assert len(token) > 0

        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        assert payload["sub"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    @patch("app.auth.settings")
    def test_token_tiene_expiracion(self, mock_settings):
        mock_settings.jwt_secret_key = SECRET
        mock_settings.jwt_expire_minutes = 30

        token = create_access_token("user")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])

        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
        assert exp > iat


class TestVerifyToken:
    """Tests para verify_token."""

    @patch("app.auth.settings")
    def test_token_valido(self, mock_settings):
        mock_settings.jwt_secret_key = SECRET
        token = jwt.encode(
            {
                "sub": "admin",
                "exp": datetime.now(UTC) + timedelta(hours=1),
                "iat": datetime.now(UTC),
            },
            SECRET,
            algorithm="HS256",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        username = verify_token(creds)
        assert username == "admin"

    @patch("app.auth.settings")
    def test_token_expirado(self, mock_settings):
        mock_settings.jwt_secret_key = SECRET
        token = jwt.encode(
            {
                "sub": "admin",
                "exp": datetime.now(UTC) - timedelta(hours=1),
                "iat": datetime.now(UTC) - timedelta(hours=2),
            },
            SECRET,
            algorithm="HS256",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(creds)
        assert exc_info.value.status_code == 401

    @patch("app.auth.settings")
    def test_token_invalido(self, mock_settings):
        mock_settings.jwt_secret_key = SECRET
        token = jwt.encode(
            {
                "sub": "admin",
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            "wrong-secret-key-must-be-at-least-32-bytes!!",
            algorithm="HS256",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(creds)
        assert exc_info.value.status_code == 401

    @patch("app.auth.settings")
    def test_token_sin_subject(self, mock_settings):
        mock_settings.jwt_secret_key = SECRET
        token = jwt.encode(
            {
                "exp": datetime.now(UTC) + timedelta(hours=1),
                "iat": datetime.now(UTC),
            },
            SECRET,
            algorithm="HS256",
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            verify_token(creds)
        assert exc_info.value.status_code == 401


class TestAuthenticateUser:
    """Tests para authenticate_user."""

    @patch("app.auth.settings")
    def test_credenciales_correctas(self, mock_settings):
        mock_settings.app_username = "admin"
        mock_settings.app_password = "secret123"
        assert authenticate_user("admin", "secret123") is True

    @patch("app.auth.settings")
    def test_usuario_incorrecto(self, mock_settings):
        mock_settings.app_username = "admin"
        mock_settings.app_password = "secret123"
        assert authenticate_user("wrong", "secret123") is False

    @patch("app.auth.settings")
    def test_password_incorrecto(self, mock_settings):
        mock_settings.app_username = "admin"
        mock_settings.app_password = "secret123"
        assert authenticate_user("admin", "wrong") is False

    @patch("app.auth.settings")
    def test_ambos_incorrectos(self, mock_settings):
        mock_settings.app_username = "admin"
        mock_settings.app_password = "secret123"
        assert authenticate_user("wrong", "wrong") is False
