import os
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import HTTPException
import secrets

# OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Scopes
GOOGLE_SCOPES = ["openid", "email", "profile"]

async def get_google_oauth_client():
    """Create Google OAuth2 client"""
    return AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

def get_google_auth_url(state: str = None):
    """Generate Google OAuth authorization URL"""
    client = AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    authorization_url, _ = client.create_authorization_url(
        GOOGLE_AUTH_URL,
        scope=GOOGLE_SCOPES,
        state=state,
    )

    return authorization_url

async def get_google_user_info(token: str):
    """Get user info from Google using access token"""
    async with AsyncOAuth2Client(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token=token,
    ) as client:
        try:
            resp = await client.get(GOOGLE_USERINFO_URL)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to get user info: {str(e)}")
