"""
Authentication utilities shared across routers
"""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET', 'erp-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
