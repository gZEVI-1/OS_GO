# auth/desktop/main.py
import sys
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QStackedWidget,
    QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon


API_BASE = "http://51.250.64.161:8000"  # URL вашего backend


class StyledInput(QLineEdit):
    def __init__(self, placeholder="", password=False):
        super().__init__()
        self.setPlaceholderText(placeholder)
        if password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setMinimumHeight(45)
        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 0 15px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #667eea;
            }
        """)


class StyledButton(QPushButton):
    def __init__(self, text, primary=True):
        super().__init__(text)
        self.setMinimumHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #5a6fd6, stop:1 #6a4190);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 #4e5fc4, stop:1 #5e3780);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #667eea;
                    border: 2px solid #667eea;
                    border-radius: 12px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #667eea;
                    color: white;
                }
            """)


class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(" OS_GO Auth")
        self.setMinimumSize(450, 600)
        self.setStyleSheet("background: #f5f5f5;")
        
        # Центральный виджет с тенью
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Карточка
        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 20px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(40, 40, 40, 40)
        
        # Заголовок
        self.title = QLabel(" Добро пожаловать")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size: 28px; font-weight: bold; color: #333;")
        card_layout.addWidget(self.title)
        
        # Переключатель экранов
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_login_widget())      # 0
        self.stack.addWidget(self.create_register_widget())   # 1
        self.stack.addWidget(self.create_2fa_widget())        # 2
        self.stack.addWidget(self.create_profile_widget())    # 3
        card_layout.addWidget(self.stack)
        
        layout.addWidget(card)
        
        self.token = None
        self.temp_token = None  # Для 2FA
        
    def create_login_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        self.login_email = StyledInput("Email")
        self.login_password = StyledInput("Пароль", password=True)
        
        layout.addWidget(QLabel("Email"))
        layout.addWidget(self.login_email)
        layout.addWidget(QLabel("Пароль"))
        layout.addWidget(self.login_password)
        
        btn_login = StyledButton("Войти")
        btn_login.clicked.connect(self.do_login)
        layout.addWidget(btn_login)
        
        btn_switch = StyledButton("Создать аккаунт", primary=False)
        btn_switch.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        layout.addWidget(btn_switch)
        
        # Auth0 кнопка
        btn_auth0 = StyledButton(" Войти через Auth0", primary=False)
        btn_auth0.clicked.connect(self.do_auth0)
        layout.addWidget(btn_auth0)
        
        layout.addStretch()
        return widget
    
    def create_register_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        self.reg_name = StyledInput("Полное имя")
        self.reg_email = StyledInput("Email")
        self.reg_password = StyledInput("Пароль (мин. 8 символов)", password=True)
        
        layout.addWidget(QLabel("Полное имя"))
        layout.addWidget(self.reg_name)
        layout.addWidget(QLabel("Email"))
        layout.addWidget(self.reg_email)
        layout.addWidget(QLabel("Пароль"))
        layout.addWidget(self.reg_password)
        
        btn_reg = StyledButton("Зарегистрироваться")
        btn_reg.clicked.connect(self.do_register)
        layout.addWidget(btn_reg)
        
        btn_back = StyledButton("Уже есть аккаунт? Войти", primary=False)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(btn_back)
        
        layout.addStretch()
        return widget
    
    def create_2fa_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        info = QLabel("Введите код из приложения-аутентификатора")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(info)
        
        self.totp_code = StyledInput("6-значный код")
        layout.addWidget(self.totp_code)
        
        btn_verify = StyledButton("Подтвердить")
        btn_verify.clicked.connect(self.do_verify_2fa)
        layout.addWidget(btn_verify)
        
        layout.addStretch()
        return widget
    
    def create_profile_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        self.profile_info = QLabel()
        self.profile_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_info.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(self.profile_info)
        
        # 2FA управление
        # Кнопка настройки 2FA
        self.btn_2fa_setup = StyledButton("🔐 Настроить 2FA"    )
        self.btn_2fa_setup.clicked.connect(self.do_setup_2fa)
        layout.addWidget(self.btn_2fa_setup)

        # QR-код (изначально скрыт)
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.hide()
        layout.addWidget(self.qr_label)

# Секрет для ручного ввода (изначально скрыт)
        self.secret_label = QLabel()
        self.secret_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secret_label.setStyleSheet("font-family: monospace; font-size: 14px; color: #667eea;")
        self.secret_label.hide()
        layout.addWidget(self.secret_label)

# Поле для ввода кода из приложения (изначально скрыто)
        self.setup_code_input = StyledInput("Введите 6-значный код")
        self.setup_code_input.hide()
        layout.addWidget(self.setup_code_input)

# Кнопка подтверждения настройки (изначально скрыта)
        self.btn_verify_setup = StyledButton("✅ Подтвердить 2FA")
        self.btn_verify_setup.clicked.connect(self.do_verify_setup)
        self.btn_verify_setup.hide()
        layout.addWidget(self.btn_verify_setup)

# Резервные коды (изначально скрыты)
        self.backup_codes = QTextEdit()
        self.backup_codes.setReadOnly(True)
        self.backup_codes.setMaximumHeight(100)
        self.backup_codes.hide()
        layout.addWidget(self.backup_codes)

# Кнопка отмены настройки (изначально скрыта)
        self.btn_cancel_setup = StyledButton("❌ Отмена", primary=False)
        self.btn_cancel_setup.clicked.connect(self.cancel_2fa_setup)
        self.btn_cancel_setup.hide()
        layout.addWidget(self.btn_cancel_setup)
        
        btn_logout = StyledButton("Выйти", primary=False)
        btn_logout.clicked.connect(self.do_logout)
        layout.addWidget(btn_logout)
        
        layout.addStretch()
        return widget
    
    def show_message(self, text, success=True):
        msg = QMessageBox(self)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Information if success else QMessageBox.Icon.Warning)
        msg.exec()
    
    # ============ API CALLS ============
    
    def do_register(self):
        data = {
            "email": self.reg_email.text(),
            "password": self.reg_password.text(),
            # "full_name": self.reg_name.text()
        }
        try:
            r = requests.post(f"{API_BASE}/auth/register", json=data, timeout=10)
            if r.status_code == 200:
                self.show_message("✅ Регистрация успешна!")
                self.stack.setCurrentIndex(0)
            else:
                self.show_message(f"❌ {r.json().get('detail', 'Ошибка')}", False)
        except Exception as e:
            self.show_message(f"❌ Ошибка соединения: {e}", False)
    
    def do_login(self):
        data = {
            "username": self.login_email.text(),
            "password": self.login_password.text()
        }
        try:
            r = requests.post(f"{API_BASE}/auth/login", data=data, timeout=10)
            result = r.json()

            print(f"DEBUG status: {r.status_code}")           # ← ДОБАВЬ
            print(f"DEBUG requires_2fa: {result.get('requires_2fa')}")  # ← ДОБАВЬ
            print(f"DEBUG access_token: {result.get('access_token', 'НЕТ')[:30]}...")
            
            if r.status_code == 200:
                if result.get("requires_2fa"):
                    # Нужна 2FA
                    self.temp_token = result["access_token"]
                    print(f"DEBUG temp_token сохранён: {self.temp_token[:30]}...")
                    self.stack.setCurrentIndex(2)
                else:
                    # Прямой вход
                    self.token = result["access_token"]
                    self.show_profile()
            else:
                self.show_message(f"❌ {result.get('detail', 'Ошибка')}", False)
        except Exception as e:
            print(f"DEBUG EXCEPTION: {e}")
            self.show_message(f"❌ Ошибка: {e}", False)
    
    def do_verify_2fa(self):
        code = self.totp_code.text()
        try:
            r = requests.post(f"{API_BASE}/auth/2fa/verify", headers={"Authorization": f"Bearer {self.temp_token}"}, json={"token": code}, timeout=10)
            result = r.json()
            
            if r.status_code == 200:
                self.token = result["access_token"]
                self.show_profile()
            else:
                self.show_message(f"❌ {result.get('detail', 'Ошибка')}", False)
        except Exception as e:
            self.show_message(f"❌ Ошибка: {e}", False)
    
    def do_auth0(self):
        # Открыть браузер для Auth0
        import webbrowser
        webbrowser.open(f"{API_BASE}/auth/auth0/login")
        self.show_message("Откройте браузер для входа через Auth0")
    
    def show_profile(self):
        try:
            r = requests.get(
                f"{API_BASE}/auth/me",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            if r.status_code == 200:
                user = r.json()
                self.profile_info.setText(
                    f"👤 {user.get('email', 'User')}\n"
                    f"📧 {user.get('email')}\n"
                    f"🔐 2FA: {'Включена' if user.get('totp_enabled') else 'Выключена'}"
                )
            
            # Скрываем элементы настройки 2FA
                self.reset_2fa_ui()
            
            # Если 2FA уже включена — скрываем кнопку настройки
                if user.get('totp_enabled'):
                    self.btn_2fa_setup.hide()
                else:
                    self.btn_2fa_setup.show()
            
                self.stack.setCurrentIndex(3)
            else:
                self.show_message("❌ Не удалось загрузить профиль", False)
        except Exception as e:
            self.show_message(f"❌ Ошибка: {e}", False)

    def reset_2fa_ui(self):
        """Скрыть элементы настройки 2FA, показать основные кнопки"""
        self.qr_label.hide()
        self.qr_label.clear()
        self.secret_label.hide()
        self.setup_code_input.hide()
        self.setup_code_input.clear()
        self.btn_verify_setup.hide()
        self.btn_cancel_setup.hide()
        self.backup_codes.hide()
        self.btn_2fa_setup.show()
        self.setup_2fa_data = None

    def do_verify_setup(self):
        """Подтверждение настройки 2FA первым кодом"""
        code = self.setup_code_input.text().strip()
    
        if len(code) != 6 or not code.isdigit():
            self.show_message("Введите 6 цифр", False)
            return
    
        try:
            r = requests.post(
                f"{API_BASE}/auth/2fa/verify-setup",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json={"token": code},
                timeout=10
            )
        
            result = r.json()
        
            if r.status_code == 200:
                self.show_message("✅ 2FA успешно включена!", True)
                self.reset_2fa_ui()
                self.show_profile()  # Обновить профиль
            else:
                self.show_message(f"❌ {result.get('detail', 'Неверный код')}", False)
            
        except Exception as e:
            self.show_message(f"❌ Ошибка: {e}", False)

    def cancel_2fa_setup(self):
        """Отмена настройки 2FA"""
        self.reset_2fa_ui()
        self.show_message("Настройка 2FA отменена", True)       

    def do_setup_2fa(self):
        try:
            r = requests.post(
                f"{API_BASE}/auth/2fa/setup",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            if r.status_code == 200:
                result = r.json()
                from PySide6.QtGui import QPixmap
                import base64
            
            # Сохраняем данные для верификации
                self.setup_2fa_data = result
            
                qr_data = result["qr_code"]      # PNG base64
                secret = result.get("secret", "")
                backup_codes = result.get("backup_codes", [])
            
            # Показываем QR-код в интерфейсе
                pixmap = QPixmap()
                pixmap.loadFromData(base64.b64decode(qr_data))
                self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
                self.qr_label.show()
            
            # Показываем секрет для ручного ввода
                formatted_secret = ' '.join(secret[i:i+4] for i in range(0, len(secret), 4))
                self.secret_label.setText(f"Секрет: {formatted_secret}")
                self.secret_label.show()
            
            # Показываем поле ввода кода и кнопки
                self.setup_code_input.show()
                self.btn_verify_setup.show()
                self.btn_cancel_setup.show()
                self.btn_2fa_setup.hide()
            
            # Показываем резервные коды
                self.backup_codes.setText("Резервные коды (сохраните!):\n" + "\n".join(backup_codes))
                self.backup_codes.show()
            
                self.show_message(
                    "1. Отсканируйте QR в Google Authenticator\n"
                    "2. Введите 6-значный код ниже\n"
                    "3. Нажмите 'Подтвердить 2FA'",
                success=True
            )
            else:
                self.show_message(f"❌ Ошибка: {r.json().get('detail', 'Неизвестная ошибка')}", False)
        except Exception as e:
            self.show_message(f"❌ Ошибка: {e}", False)
    
    def do_logout(self):
        self.token = None
        self.temp_token = None
        self.stack.setCurrentIndex(0)
        self.login_email.clear()
        self.login_password.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = AuthWindow()
    window.show()
    sys.exit(app.exec())