from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import auth, models
from .auth import AuthenticationError
from .database import SessionLocal

http_bearer = HTTPBearer(auto_error=True)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> models.User:
    token_payload = auth.decode_access_token(credentials.credentials)
    user = db.query(models.User).filter(models.User.email == token_payload.sub).first()
    if not user:
        raise AuthenticationError()
    return user


def get_current_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_admin:
        raise AuthenticationError(detail="Not enough permissions")
    return current_user
