# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.user import User
from app.services.password_service import password_service
from app.services.totp_service import totp_service
from app.services.email_service import email_service
from app.dependencies.auth import (
    verify_auth0_token,
    create_internal_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str = None
    last_name: str = None


class TOTPSetupResponse(BaseModel):
    secret: str  # Показываем один раз для manual entry
    qr_code: str  # base64 SVG
    backup_codes: list[str]  # Показываем один раз


class TOTPVerifyRequest(BaseModel):
    token: str  # 6-значный код


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    requires_2fa: bool = False


# ========== Регистрация и вход ==========

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Регистрация нового пользователя с локальным паролем"""
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed = password_service.hash_password(data.password)
    verification_token = email_service.generate_verification_token()
    token_expires = datetime.now(timezone.utc) + timedelta(hours=24)

    user = User(
        email=data.email,
        hashed_password=hashed.encode(),
        is_verified=False,
        verification_token=verification_token,
        verification_token_expires=token_expires,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    background_tasks.add_task(
        email_service.send_verification_email,
        data.email,
        verification_token,
    )

    return {"message": "Registration successful. Please check your email to verify your account."}


@router.post("/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Локальный вход с поддержкой 2FA"""
    # Поиск пользователя
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Проверка пароля
    if not password_service.verify_password(
        form_data.password, 
        user.hashed_password.decode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox.",
            headers={"X-Email-Verification-Required": "true"},
        )

    if user.totp_enabled:
        temp_token = create_internal_token(
            user.id, 
            user.email, 
            totp_verified=False
        )
        return {
            **temp_token,
            "requires_2fa": True
        }
    
    # Обычный вход
    tokens = create_internal_token(user.id, user.email, totp_verified=True)
    return {**tokens, "requires_2fa": False}


@router.post("/auth0/callback", response_model=LoginResponse)
async def auth0_callback(
    auth0_payload: dict = Depends(verify_auth0_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Обработка callback от Auth0
    Создаёт или связывает локального пользователя с Auth0
    """
    auth0_id = auth0_payload.get("sub")
    email = auth0_payload.get("email")
    
    # Поиск по Auth0 ID
    result = await db.execute(
        select(User).where(User.auth0_id == auth0_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Поиск по email для связывания
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Связываем существующего пользователя
            user.auth0_id = auth0_id
        else:
            # Создаём нового пользователя
            user = User(
                email=email,
                auth0_id=auth0_id,
                is_verified=auth0_payload.get("email_verified", False)
            )
            db.add(user)
        
        await db.commit()
        await db.refresh(user)
    
    # Проверка 2FA
    if user.totp_enabled:
        tokens = create_internal_token(user.id, user.email, totp_verified=False)
        return {**tokens, "requires_2fa": True}
    
    tokens = create_internal_token(user.id, user.email, totp_verified=True)
    return {**tokens, "requires_2fa": False}


# ========== 2FA Management ==========

@router.post("/2fa/setup", response_model=TOTPSetupResponse)
async def setup_2fa(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Настройка TOTP 2FA"""
    user_id = int(current_user["sub"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    if user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA already enabled"
        )
    
    # Генерация секрета
    secret = totp_service.generate_secret()
    encrypted_secret = totp_service.encrypt_secret(secret)
    
    # Генерация backup кодов
    backup_codes, encrypted_backup = totp_service.generate_backup_codes()
    
    # Сохраняем (но пока не активируем - требуется верификация)
    user.totp_secret = encrypted_secret
    user.backup_codes = encrypted_backup
    
    await db.commit()
    
    # Генерация QR
    uri = totp_service.generate_provisioning_uri(secret, user.email)
    qr_code = totp_service.generate_qr_code(uri)
    
    return TOTPSetupResponse(
        secret=secret,  # Для manual entry
        qr_code=qr_code,
        backup_codes=backup_codes  # Показываем один раз!
    )


@router.post("/2fa/verify-setup")
async def verify_2fa_setup(
    data: TOTPVerifyRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтверждение настройки 2FA первым кодом"""
    user_id = int(current_user["sub"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    secret = totp_service.decrypt_secret(user.totp_secret)
    
    if not totp_service.verify_totp(secret, data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )
    
    # Активируем 2FA
    user.totp_enabled = True
    user.totp_verified = True
    await db.commit()
    
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/verify")
async def verify_2fa(
    data: TOTPVerifyRequest,
    temp_token: str,  # Временный токен из login
    db: AsyncSession = Depends(get_db)
):
    """Верификация 2FA при входе"""
    # Декодируем временный токен
    from jose import jwt, JWTError
    from config import get_settings
    
    settings = get_settings()
    
    try:
        payload = jwt.decode(
            temp_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid temporary token"
        )
    
    if payload.get("totp_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA already verified"
        )
    
    user_id = int(payload["sub"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not configured"
        )
    
    secret = totp_service.decrypt_secret(user.totp_secret)
    
    # Проверяем TOTP или backup code
    is_valid = totp_service.verify_totp(secret, data.token)
    
    if not is_valid:
        # Проверяем backup code
        is_valid, new_backup_data = totp_service.verify_backup_code(
            data.token,
            user.backup_codes
        )
        if is_valid:
            user.backup_codes = new_backup_data
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code"
        )
    
    # Выдаём полноценный токен
    tokens = create_internal_token(user.id, user.email, totp_verified=True)
    return tokens


@router.post("/2fa/disable")
async def disable_2fa(
    data: TOTPVerifyRequest,  # Требуем код для отключения
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отключение 2FA (требует подтверждение)"""
    user_id = int(current_user["sub"])
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    if not user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled"
        )
    
    # Проверяем код перед отключением
    secret = totp_service.decrypt_secret(user.totp_secret)
    if not totp_service.verify_totp(secret, data.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )
    
    # Очищаем 2FA данные
    user.totp_secret = None
    user.totp_enabled = False
    user.totp_verified = False
    user.backup_codes = None
    
    await db.commit()
    
    return {"message": "2FA disabled successfully"}


# ========== Email Verification ==========

@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Верификация email по ссылке из письма"""
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    if user.is_verified:
        return {"message": "Email already verified"}

    if user.verification_token_expires and user.verification_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired. Request a new one.",
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    await db.commit()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    data: dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Повторная отправка письма верификации"""
    email = data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    new_token = email_service.generate_verification_token()
    user.verification_token = new_token
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.commit()

    background_tasks.add_task(
        email_service.send_verification_email,
        email,
        new_token,
    )

    return {"message": "Verification email sent"}


# ========== Защищённые эндпоинты ==========

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Получение данных текущего пользователя"""
    user_id = int(current_user["sub"])
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": user.id,
        "email": user.email,
        "is_verified": user.is_verified,
        "totp_enabled": user.totp_enabled,
    }


@router.get("/protected")
async def protected_route(
    current_user: dict = Depends(get_current_user)
):
    """Пример защищённого маршрута"""
    return {
        "message": "Access granted",
        "user": current_user["email"]
    }