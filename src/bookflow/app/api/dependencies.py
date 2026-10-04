import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from bookflow.app.core.security import decode_access_token
from bookflow.app.database.session import get_db
from bookflow.app.models import User


bearer_scheme = HTTPBearer()

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    db: DbSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = uuid.UUID(subject)

    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user