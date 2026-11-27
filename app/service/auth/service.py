import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.model.models import User
from app.service.auth import crud
from app.service.auth.schema import LoginRequest, SignupRequest

SESSION_TTL = timedelta(days=7)

hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash(secrets.token_urlsafe(16))


class EmailTakenError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def signup(db: Session, data: SignupRequest) -> User:
    email = normalize_email(data.email)
    if crud.get_user_by_email(db, email) is not None:
        raise EmailTakenError
    try:
        return crud.create_user(
            db,
            email=email,
            password_hash=hasher.hash(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
        )
    except IntegrityError as exc:
        db.rollback()
        raise EmailTakenError from exc


def login(db: Session, data: LoginRequest) -> tuple[User, str]:
    user = crud.get_user_by_email(db, normalize_email(data.email))
    if user is None:
        hasher.verify(data.password, DUMMY_HASH)
        raise InvalidCredentialsError
    if not hasher.verify(data.password, user.password_hash):
        raise InvalidCredentialsError

    token = secrets.token_urlsafe(32)
    crud.create_user_session(
        db,
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + SESSION_TTL,
    )
    return user, token


def user_from_token(db: Session, token: str) -> User | None:
    user_session = crud.get_active_session(db, hash_token(token), datetime.now(UTC))
    return None if user_session is None else user_session.user


def logout(db: Session, token: str) -> None:
    user_session = crud.get_active_session(db, hash_token(token), datetime.now(UTC))
    if user_session is not None:
        crud.revoke_session(db, user_session)
