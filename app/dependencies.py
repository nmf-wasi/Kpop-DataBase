from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from app.database.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.security.tokens import decode_token
from jose import JWTError
from app.models.models import User
from app.schemas.user import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """When used, just returns the current user using JWT Token validation"""

    # we need to do same exeption multiple tiems, so better make it a var
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not valiate credentials!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # try decoding the token
        payload = decode_token(token)
        username: str | None = payload.get("sub")
        # check if user is none
        if username is None:
            raise credentials_exception
    except JWTError:  # if token is corrupted
        raise credentials_exception

    # query db for username
    user = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    # if can't find user, rasise exception
    if not user:
        raise credentials_exception
    # if user found, return the user
    return user


def require_role(*allowed_roles: UserRole):
    """Takes the required roles, finds the current user, checks if the current user has the required roles and returns the user if current user has that role, else raises Exception as Forbidden"""

    # wrapper func
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


# *allowed_roles means you can call require_role(UserRole.ADMIN)
# for admin-only routes, or require_role
# (UserRole.ADMIN, UserRole.USER) for routes multiple roles can access
