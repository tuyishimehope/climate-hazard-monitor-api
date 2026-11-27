from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.model.models import User
from app.service.auth import service
from app.service.auth.schema import LoginRequest, SignupRequest, UserResponse

AUTH_ROUTER = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_NAME = "session_id"

DbSession = Annotated[Session, Depends(get_session)]
SessionToken = Annotated[str | None, Cookie(alias=COOKIE_NAME)]


def current_user(db: DbSession, token: SessionToken = None) -> User:
    user = None if token is None else service.user_from_token(db, token)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@AUTH_ROUTER.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def signup(data: SignupRequest, db: DbSession) -> User:
    try:
        return service.signup(db, data)
    except service.EmailTakenError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An account with this email already exists"
        ) from exc


@AUTH_ROUTER.post("/login", response_model=UserResponse)
def login(data: LoginRequest, response: Response, db: DbSession) -> User:
    try:
        user, token = service.login(db, data)
    except service.InvalidCredentialsError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid email or password"
        ) from exc
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(service.SESSION_TTL.total_seconds()),
        httponly=True,
        samesite="lax",
    )
    return user


@AUTH_ROUTER.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, db: DbSession, token: SessionToken = None) -> None:
    if token is not None:
        service.logout(db, token)
    response.delete_cookie(COOKIE_NAME)


@AUTH_ROUTER.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> User:
    return user
