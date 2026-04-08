# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    
    # Локальная аутентификация
    hashed_password = Column(LargeBinary, nullable=True)
    
    # Auth0 связь
    auth0_id = Column(String(255), unique=True, nullable=True)
    
    # 2FA
    totp_secret = Column(LargeBinary, nullable=True)  # Зашифрованный секрет
    totp_enabled = Column(Boolean, default=False)
    totp_verified = Column(Boolean, default=False)
    backup_codes = Column(LargeBinary, nullable=True)  # Зашифрованные backup codes
    
    # Статус
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)