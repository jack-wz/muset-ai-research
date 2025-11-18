"""User API endpoints."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update current user.

    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user information
    """
    # Update user fields
    if user_update.name is not None:
        current_user.name = user_update.name

    if user_update.avatar is not None:
        current_user.avatar = user_update.avatar

    if user_update.settings is not None:
        current_user.settings = user_update.settings

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get user by ID.

    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        User information

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
