from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.models import User
from app.core.auth import get_db
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get list of users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"detail": "User not found"}
    return user



