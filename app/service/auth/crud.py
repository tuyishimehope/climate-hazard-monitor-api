from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.model.models import SessionStatus, User, UserSession


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(
    db: Session,
    *,
    email: str,
    password_hash: str,
    first_name: str | None,
    last_name: str | None,
) -> User:
    user = User(
        email=email,
        password_hash=password_hash,
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_user_session(
    db: Session, *, user_id: int, token_hash: str, expires_at: datetime
) -> UserSession:
    user_session = UserSession(
        user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
    db.add(user_session)
    db.commit()
    return user_session


def get_active_session(
    db: Session, token_hash: str, now: datetime
) -> UserSession | None:
    return db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_hash,
            UserSession.status == SessionStatus.ACTIVE,
            UserSession.expires_at > now,
        )
    )


def revoke_session(db: Session, user_session: UserSession) -> None:
    user_session.status = SessionStatus.REVOKED
    db.commit()
