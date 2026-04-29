# app/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

# Загружаем .env вручную ПЕРЕД импортом Settings
BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"

print(f"📁 Loading .env from: {ENV_PATH}")
print(f"✅ File exists: {ENV_PATH.exists()}")

if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
    # Проверим что загрузилось
    print(f"🔍 DATABASE_URL from os.environ: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")
else:
    print("⚠️ .env not found!")


class Settings(BaseSettings):
    # App
    app_name: str = "Auth Service"
    debug: bool = False
    secret_key: str = "default-secret-change-me"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./fallback.db"
    
    # Auth0
    auth0_domain: str = ""
    auth0_api_audience: str = ""
    auth0_issuer: str = ""
    auth0_algorithms: list = ["RS256"]
    
    # JWT
    jwt_secret: str = "default-jwt-secret"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Password Hashing
    password_hash_scheme: str = "argon2"
    bcrypt_rounds: int = 12
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4
    
    # 2FA
    totp_issuer_name: str = "YourApp"
    totp_digits: int = 6
    totp_interval: int = 30
    
    # Email / SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    
    # Верификация
    verification_token_expire_hours: int = 24
    app_url: str = "http://localhost:8000"
    
    # НОВАЯ КОНФИГУРАЦИЯ для pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ← игнорируем лишние переменные
        populate_by_name=True,
    )


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    print(f"✅ Settings loaded! DB: {settings.database_url[:50]}...")
    return settings


# Для теста
if __name__ == "__main__":
    s = get_settings()
    print(f"\nDebug: {s.debug}")
    print(f"Database: {s.database_url}")