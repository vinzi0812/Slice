from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from app.db.models import User
from app.core.config import get_google_auth_url, exchange_code_for_token, get_google_user_info
from app.core.auth import create_access_token, get_db, get_current_user, get_password_hash, verify_password
from app.schemas.user import UserResponse, UserCreate, LoginRequest
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
        # Exchange authorization code for access token
        token = await exchange_code_for_token(code)

        # Fetch actual user info from Google using the access token
        user_info = await get_google_user_info(token)

        # Check if user exists, if not create them
        user = db.query(User).filter(User.email == user_info["email"]).first()
        full_name = user_info.get("name", "")
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        profile_picture = user_info.get("picture")

        if not user:
            # Generate username from email (before @)
            username = user_info["email"].split("@")[0]

            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                name=full_name,
                email=user_info["email"],
                profile_picture=profile_picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Keep Google-backed user metadata fresh on each login.
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            user.name = full_name or user.name
            if profile_picture:
                user.profile_picture = profile_picture
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

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Log out the current user.

    JWT auth is stateless in this app, so logout is completed client-side by
    discarding the token after the server confirms the request is authenticated.
    """
    return {"message": "Logged out successfully"}

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.username:
        existing_username = db.query(User).filter(User.username == user.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")

    # Hash password if provided
    password_hash = None
    if user.password:
        password_hash = get_password_hash(user.password)

    # Create new user
    db_user = User(
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        name=user.name,
        email=user.email,
        password_hash=password_hash,
        phone_number=user.phone_number,
        profile_picture=user.profile_picture
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    identifier = request.identifier.strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Username or email is required")

    normalized_identifier = identifier.lower()
    user = (
        db.query(User)
        .filter(
            or_(
                func.lower(User.email) == normalized_identifier,
                func.lower(User.username) == normalized_identifier,
            )
        )
        .first()
    )
    if not user or not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": user.name,
            "email": user.email,
            "phone_number": user.phone_number,
            "profile_picture": user.profile_picture,
            "created_at": user.created_at,
        },
    }
