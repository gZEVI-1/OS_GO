# test_env.py
import os
import sys

# Показать откуда запускаемся
print(f"Current directory: {os.getcwd()}")
print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")

# Проверить есть ли .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
print(f"Looking for .env at: {env_path}")
print(f".env exists: {os.path.exists(env_path)}")

# Попробовать загрузить
try:
    from app.config import get_settings
    settings = get_settings()
    
    print(f"\n✅ Settings loaded!")
    print(f"Database URL: {settings.database_url}")
    print(f"Debug mode: {settings.debug}")
    print(f"Auth0 Domain: {settings.auth0_domain or 'NOT SET'}")
    
except Exception as e:
    print(f"\n❌ Error loading settings: {e}")
    import traceback
    traceback.print_exc()
