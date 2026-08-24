from fastapi import APIRouter, Depends
from app.schemas.user import (
    UserResponse,
    UserCreate,
    UserUpdate,
    LoginResponse,
    RefreshRequest,
)
from sqlalchemy.orm import Session
from app.database.database import get_db
from sqlalchemy import select, func
from app.models import models
from fastapi import HTTPException, status
from app.security.password import hash_password, verify_password
from fastapi.security import OAuth2PasswordRequestForm
from app.security.tokens import create_access_token, create_refresh_token, decode_token
from app.dependencies import get_current_user, require_role
from jose import JWTError
from app.config.enums import UserRole
from datetime import datetime
router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.execute(select(models.User)).scalars().all()


@router.post("/create_user", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.execute(
        select(models.User).where(models.User.username == user_data.username)
    ).scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists!",
        )
    user = db.execute(
        select(models.User).where(models.User.email == user_data.email)
    ).scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered!",
        )
    hashed_password = hash_password(user_data.password)
    new_user = models.User()
    for key, val in user_data.model_dump().items():
        if key == "password":
            continue
        setattr(new_user, key, val)

    new_user.hashed_password = hashed_password
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=LoginResponse)
def login(
    user_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # OAuth2PasswordRequestForm : takes username & password
    # find the user
    user = db.execute(
        select(models.User).where(models.User.username == user_data.username)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Check username or password and try again!",
        )
    # if user exists, verifty password
    verification = verify_password(user_data.password, user.hashed_password)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Check username or password and try again!",
        )

    # add the login time to db
    user.last_login=datetime.now()
    db.commit()
    db.refresh(user)

    # create access and refresh token and return them as LoginResponse
    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token({"sub": user.username})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/refresh", response_model=LoginResponse)
def refresh_access_token(request: RefreshRequest, db: Session = Depends(get_db)):
    try:
        # find the username from payload and find user with it
        payload = decode_token(request.refresh_token)
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Refresh Token!",
            )

    except JWTError:  # if token is corrupted
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Refesh Token!"
        )
    # get the user
    user = db.execute(
        select(models.User).where(models.User.username == username)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )

    # create new access token
    access_token = create_access_token({"sub": user.username})
    # create refresh token
    refresh_token = create_refresh_token({"sub": user.username})
    # return both as login response
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """A user can delete themselves, or an admin can delete them"""
    # find user
    user = db.execute(
        select(models.User).where(models.User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )
    # if current user is not deleting themesleves and he is not an admin, raise error
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't delete other users unless you are an admin!",
        )
    # check the user being deleted is an admin or not
    # if curent user is admin, and wants to delete themselves, at first check if there are any more admins left
    if user.role == UserRole.ADMIN:
        admins = db.execute(
            select(func.count())
            .select_from(models.User)
            .where(models.User.role == UserRole.ADMIN)
        ).scalar()

        if admins is None:
            admins = 0
        if admins < 2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete the last admin!",
            )
    db.delete(user)
    db.commit()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Admin or user themselves can update their profile, however, we won't let users change password here, that has a separate endpoint"""
    # check if the use exists
    user = db.execute(
        select(models.User).where(models.User.id == user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )
    # check if the current user is modifying themsleves or they are admin or not
    if current_user.id != user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't modify other user's info!",
        )

    # if the current user is admin, let them through, we aren't letting them change their roles, so we don't need to check last admin

    # check if the new username is unique
    if user_data.username:
        existing_user = db.execute(
            select(models.User).where(
                models.User.username == user_data.username, models.User.id != user.id
            )  # if user sends same username, then it's not an issue
        ).scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That username is already registered!",
            )
    # check if the new email is unique
    if user_data.email:
        existing_user = db.execute(
            select(models.User).where(
                models.User.email == user_data.email, models.User.id != user.id
            )  # if user sends same email, then it's not an issue
        ).scalar_one_or_none()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That email is already registered!",
            )

    # take the updated data and add it to the existing user
    updated_data = user_data.model_dump(exclude_unset=True)
    for key, val in updated_data.items():
        setattr(user, key, val)

    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id:int,
    new_role:UserRole,
    db:Session=Depends(get_db),
    current_user:models.User=Depends(require_role(UserRole.ADMIN))
):
    """An admin can change role of other users, including themselves and other admins"""
    # check if user exists
    user=db.execute(
        select(models.User)
        .where(models.User.id==user_id)
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found!",
        )

    # no need to check if the current user is admin or not, dependency added confirms that only admins can access this end point
    # check if we are making someone user
    if new_role!=UserRole.ADMIN and user.role==UserRole.ADMIN:
        admin_count=db.execute(
            select(func.count())
            .select_from(models.User)
            .where(models.User.role==UserRole.ADMIN)
        ).scalar()

        if admin_count is None:
            admin_count=0

        if admin_count<2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot demote the last remaining admin!",
            )
    user.role=new_role
    db.commit()
    db.refresh(user)
    return user
