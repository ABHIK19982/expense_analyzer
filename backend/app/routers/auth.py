"""Auth API routes (cookie session)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models.user import User
from app.schemas import (
    LoginRequest,
    MeResponse,
    MessageResponse,
    SignupRequest,
    UserResponse,
)
from app.services.auth import authenticate, create_user, validate_credentials
from app.services.dynamodb import get_last_three_months

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MessageResponse)
def login(
    body: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    if not validate_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad format of username or password",
        )

    user = authenticate(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    request.session.clear()
    request.session["user_id"] = user.uid
    return MessageResponse(message="Logged in successfully", status="ok")


@router.post("/signup", response_model=MessageResponse)
def signup(
    body: SignupRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    if not validate_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad format of username or password",
        )

    result = create_user(
        db,
        {
            "username": body.username,
            "password": body.password,
            "email": body.email,
            "fname": body.fname,
            "lname": body.lname,
            "fam_size": body.fam_size,
        },
    )
    if result == "User Already Exists":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User Already Exists",
        )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error in creating user",
        )
    return MessageResponse(message="User Created Successfully", status="ok")


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    _user: User = Depends(get_current_user),
) -> MessageResponse:
    request.session.clear()
    return MessageResponse(message="Logged out successfully", status="ok")


@router.get("/me", response_model=MeResponse)
def me(
    user: User | None = Depends(get_optional_user),
) -> MeResponse:
    if user is None:
        return MeResponse(authenticated=False)
    return MeResponse(
        authenticated=True,
        username=user.username,
        uid=user.uid,
        months=get_last_three_months(),
    )


@router.get("/profile", response_model=UserResponse)
def profile(user: User = Depends(get_current_user)) -> User:
    return user
