from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User
from .oauth_config import get_google_auth_url
from .auth_utils import create_access_token, get_db, get_current_user
import secrets

router = APIRouter()

@router.get("/google/login")
async def google_login():
    """Initiate Google OAuth login"""
    state = secrets.token_urlsafe(32)  # Generate random state for security
    auth_url = get_google_auth_url(state)
    return {"auth_url": auth_url, "state": state}

@router.get("/google/callback")
async def google_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Here you would exchange the code for tokens
        # For simplicity, we'll simulate this - in production you'd use the OAuth client

        # Mock user info - replace with actual Google user info
        user_info = {
            "id": "google_123",
            "email": "user@gmail.com",
            "name": "John Doe",
            "picture": "https://example.com/photo.jpg"
        }

        # Check if user exists, if not create them
        user = db.query(User).filter(User.email == user_info["email"]).first()

        if not user:
            user = User(
                name=user_info["name"],
                email=user_info["email"],
                profile_picture=user_info.get("picture")
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create JWT token
        access_token = create_access_token(data={"sub": user.id})

        # Redirect to frontend with token
        frontend_url = "http://localhost:5173/auth/callback"
        return RedirectResponse(
            url=f"{frontend_url}?token={access_token}&user_id={user.id}",
            status_code=302
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "profile_picture": current_user.profile_picture,
        "created_at": current_user.created_at
    }
