from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.services import auth_service, token_service
from app.config import settings

router = APIRouter()

_COOKIE_OPTS: dict = {
    "httponly": True,
    "samesite": "lax",
    "path": "/",
}


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    secure = settings.ENVIRONMENT == "production"
    response.set_cookie(
        "access_token", access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=secure, **_COOKIE_OPTS
    )
    response.set_cookie(
        "refresh_token", refresh_token, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        secure=secure, **_COOKIE_OPTS
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    request_body: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await auth_service.register_user(db, request_body)
    access_token = token_service.create_access_token(user.id)
    refresh_token = await auth_service.create_and_store_refresh_token(db, user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return UserOut.model_validate(user)


@router.post("/login", response_model=UserOut)
async def login(
    request_body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    user = await auth_service.authenticate_user(db, request_body.email, request_body.password)
    access_token = token_service.create_access_token(user.id)
    refresh_token = await auth_service.create_and_store_refresh_token(db, user.id)
    _set_auth_cookies(response, access_token, refresh_token)
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> None:
    raw_token = request.cookies.get("refresh_token")
    if raw_token:
        await auth_service.logout_user(db, raw_token)
    _clear_auth_cookies(response)


@router.post("/refresh", response_model=UserOut)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise CredentialsException()

    user, new_refresh_token = await auth_service.validate_and_rotate_refresh_token(db, raw_token)
    new_access_token = token_service.create_access_token(user.id)
    _set_auth_cookies(response, new_access_token, new_refresh_token)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
