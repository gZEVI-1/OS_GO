# app/services/totp_service.py
import pyotp
import qrcode
import qrcode.image.svg
import io
import base64
import secrets
import json
from cryptography.fernet import Fernet
from app.config import get_settings


class TOTPService:
    def __init__(self):
        self.settings = get_settings()
        import hashlib
        key_bytes = self.settings.secret_key.encode()
        raw_key = hashlib.sha256(key_bytes).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(raw_key))
    
    def generate_secret(self) -> str:
        """Генерация нового TOTP секрета"""
        return pyotp.random_base32()
    
    def encrypt_secret(self, secret: str) -> bytes:
        """Шифрование секрета для хранения в БД"""
        return self.cipher.encrypt(secret.encode())
    
    def decrypt_secret(self, encrypted_secret: bytes) -> str:
        """Расшифровка секрета"""
        return self.cipher.decrypt(encrypted_secret).decode()
    
    def generate_provisioning_uri(
        self, 
        secret: str, 
        email: str, 
        issuer: str = None
    ) -> str:
        """Генерация URI для QR-кода"""
        issuer = issuer or self.settings.totp_issuer_name
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer
        )
    
    def generate_qr_code(self, provisioning_uri: str) -> str:
        """Генерация QR-кода в base64"""
        factory = qrcode.image.svg.SvgImage
        qr = qrcode.make(provisioning_uri, image_factory=factory)
        
        buffer = io.BytesIO()
        qr.save(buffer)
        svg_data = buffer.getvalue().decode()
        
        return base64.b64encode(svg_data.encode()).decode()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """Проверка TOTP токена"""
        totp = pyotp.TOTP(secret)
        # Проверяем текущее и соседние окна (±1) для компенсации временного сдвига
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> tuple:
        """
        Генерация одноразовых backup кодов
        Возвращает: (список отображаемых кодов, зашифрованные данные для хранения)
        """
        codes = []
        hashed_codes = []
        
        for _ in range(count):
            # Формат: XXXX-XXXX-XXXX (легко вводить)
            code = '-'.join([
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper(),
                secrets.token_hex(2).upper()
            ])
            codes.append(code)
            # Хешируем для хранения (используем SHA256 для скорости проверки)
            import hashlib
            hashed = hashlib.sha256(code.encode()).hexdigest()
            hashed_codes.append(hashed)
        
        encrypted_data = self.cipher.encrypt(
            json.dumps(hashed_codes).encode()
        )
        
        return codes, encrypted_codes
    
    def verify_backup_code(self, code: str, encrypted_data: bytes) -> tuple:
        """
        Проверка backup кода
        Возвращает: (valid: bool, new_encrypted_data: bytes или None)
        """
        import hashlib
        
        hashed_input = hashlib.sha256(code.encode()).hexdigest()
        hashed_codes = json.loads(
            self.cipher.decrypt(encrypted_data).decode()
        )
        
        if hashed_input in hashed_codes:
            # Удаляем использованный код
            hashed_codes.remove(hashed_input)
            new_data = self.cipher.encrypt(
                json.dumps(hashed_codes).encode()
            )
            return True, new_data
        
        return False, None


totp_service = TOTPService()