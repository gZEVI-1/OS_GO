# app/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.config import get_settings

security = HTTPBearer()

async def verify_auth0_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Верификация токена Auth0"""
    settings = get_settings()
    token = credentials.credentials
    
    # Получаем JWKS от Auth0
    async with httpx.AsyncClient() as client:
        jwks_url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
        jwks_response = await client.get(jwks_url)
        jwks = jwks_response.json()
    
    # Верификация подписи и claims
    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
        
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_api_audience,
            issuer=settings.auth0_issuer
        )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


def create_internal_token(user_id: int, email: str, totp_verified: bool = False) -> dict:
    """Создание внутреннего JWT после успешной аутентификации"""
    from datetime import datetime, timedelta
    
    settings = get_settings()
    now = datetime.utcnow()
    
    access_payload = {
        "sub": str(user_id),
        "email": email,
        "totp_verified": totp_verified,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes)
    }
    
    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days)
    }
    
    return {
        "access_token": jwt.encode(
            access_payload, 
            settings.jwt_secret, 
            algorithm=settings.jwt_algorithm
        ),
        "refresh_token": jwt.encode(
            refresh_payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        ),
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Получение текущего пользователя из внутреннего JWT"""
    settings = get_settings()
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Проверка 2FA если требуется
        if payload.get("totp_enabled") and not payload.get("totp_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="2FA verification required",
                headers={"X-2FA-Required": "true"}
            )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )