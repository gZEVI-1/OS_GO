# app/services/password_service.py
from passlib.context import CryptContext
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.config import get_settings


class PasswordService:
    def __init__(self):
        self.settings = get_settings()
        self._init_hasher()
    
    def _init_hasher(self):
        scheme = self.settings.password_hash_scheme
        
        if scheme == "bcrypt":
            self.pwd_context = CryptContext(
                schemes=["bcrypt"],
                bcrypt__rounds=self.settings.bcrypt_rounds
            )
            self._use_argon2 = False
        else:
            self.argon2 = PasswordHasher(
                time_cost=self.settings.argon2_time_cost,
                memory_cost=self.settings.argon2_memory_cost,
                parallelism=self.settings.argon2_parallelism,
                hash_len=32,
                salt_len=16
            )
            self._use_argon2 = True
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        if self._use_argon2:
            return self.argon2.hash(password)
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            if self._use_argon2:
                self.argon2.verify(hashed_password, plain_password)
                # Проверяем, нужен ли рехеш (параметры изменились)
                if self.argon2.check_needs_rehash(hashed_password):
                    return True  # Сигнализируем о необходимости обновления хеша
                return True
            else:
                return self.pwd_context.verify(plain_password, hashed_password)
        except (VerifyMismatchError, Exception):
            return False
    
    def needs_rehash(self, hashed_password: str) -> bool:
        """Проверка необходимости рехеширования"""
        if self._use_argon2:
            return self.argon2.check_needs_rehash(hashed_password)
        return False


password_service = PasswordService()