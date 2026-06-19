"""Router de autenticación — POST /auth/login."""

from fastapi import APIRouter, HTTPException, status

from app.auth import authenticate_user, create_access_token
from app.models import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Autentica un usuario y retorna un token JWT.

    Valida las credenciales contra las variables de entorno
    APP_USERNAME y APP_PASSWORD.
    """
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    token = create_access_token(request.username)
    return TokenResponse(access_token=token)
