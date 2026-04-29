# auth_gui.py
import customtkinter as ctk
from tkinter import messagebox, StringVar
import requests
import re
import json
from dataclasses import dataclass
from typing import Optional, Callable
from PIL import Image, ImageTk
import io
import base64
import webbrowser


# Конфигурация API
API_BASE_URL = "http://localhost:8000"
THEME_COLOR = "#3B82F6"  # Синий
SUCCESS_COLOR = "#10B981"  # Зелёный
ERROR_COLOR = "#EF4444"    # Красный
BG_COLOR = "#0F172A"       # Тёмно-синий фон
CARD_BG = "#1E293B"        # Фон карточек


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthManager:
    """Менеджер аутентификации с API"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.tokens: Optional[AuthTokens] = None
        self.current_user: Optional[dict] = None
        self.session = requests.Session()
    
    def register(self, email: str, password: str) -> tuple[bool, str]:
        """Регистрация нового пользователя"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json={"email": email, "password": password},
                timeout=10
            )
            
            if response.status_code == 201:
                return True, "Регистрация успешна! Теперь войдите в систему."
            elif response.status_code == 409:
                return False, "Этот email уже зарегистрирован"
            elif response.status_code == 400:
                detail = response.json().get("detail", "Ошибка валидации")
                return False, detail
            else:
                return False, f"Ошибка сервера: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Нет подключения к серверу. Проверьте, запущен ли API."
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def login(self, email: str, password: str, totp_code: str = "") -> tuple[bool, str, Optional[dict]]:
        """Вход в систему"""
        try:
            payload = {"email": email, "password": password}
            if totp_code:
                payload["totp_code"] = totp_code
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                timeout=10
            )
            
            data = response.json()
            
            if response.status_code == 200:
                # Проверяем, требуется ли 2FA
                if data.get("requires_2fa"):
                    return True, "requires_2fa", {
                        "temp_token": data.get("temp_token"),
                        "message": "Требуется код двухфакторной аутентификации"
                    }
                
                # Сохраняем токены
                self.tokens = AuthTokens(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_in=data["expires_in"]
                )
                
                # Получаем данные пользователя
                self.current_user = self.get_me()
                
                return True, "success", self.current_user
                
            elif response.status_code == 401:
                return False, "Неверный email или пароль", None
            else:
                detail = data.get("detail", "Ошибка авторизации")
                return False, detail, None
                
        except requests.exceptions.ConnectionError:
            return False, "Нет подключения к серверу", None
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None
    
    def verify_2fa(self, code: str, temp_token: str) -> tuple[bool, str]:
        """Подтверждение 2FA при входе"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/2fa/verify",
                json={"code": code},
                headers={"Authorization": f"Bearer {temp_token}"},
                timeout=10
            )
            
            data = response.json()
            
            if response.status_code == 200:
                self.tokens = AuthTokens(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_in=data["expires_in"]
                )
                self.current_user = self.get_me()
                return True, "Вход выполнен успешно"
            else:
                return False, data.get("detail", "Неверный код")
                
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def setup_2fa(self) -> tuple[bool, dict]:
        """Настройка 2FA"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/2fa/setup",
                headers={"Authorization": f"Bearer {self.tokens.access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"error": response.json().get("detail", "Ошибка")}
                
        except Exception as e:
            return False, {"error": str(e)}
    
    def verify_2fa_setup(self, code: str) -> tuple[bool, str]:
        """Подтверждение настройки 2FA"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/2fa/verify-setup",
                json={"code": code},
                headers={"Authorization": f"Bearer {self.tokens.access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                # Обновляем токены
                data = response.json()
                self.tokens = AuthTokens(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_in=data["expires_in"]
                )
                return True, "Двухфакторная аутентификация включена"
            else:
                return False, response.json().get("detail", "Неверный код")
                
        except Exception as e:
            return False, str(e)
    
    def get_me(self) -> Optional[dict]:
        """Получение данных текущего пользователя"""
        try:
            response = self.session.get(
                f"{self.base_url}/auth/me",
                headers={"Authorization": f"Bearer {self.tokens.access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def logout(self):
        """Выход из системы"""
        try:
            if self.tokens:
                self.session.post(
                    f"{self.base_url}/auth/logout",
                    headers={"Authorization": f"Bearer {self.tokens.access_token}"}
                )
        except:
            pass
        finally:
            self.tokens = None
            self.current_user = None


class ModernAuthApp(ctk.CTk):
    """Главное окно приложения аутентификации"""
    
    def __init__(self):
        super().__init__()
        
        # Настройки окна
        self.title("SecureAuth - Вход и Регистрация")
        self.geometry("500x700")
        self.resizable(False, False)
        
        # Цвета
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Менеджер аутентификации
        self.auth = AuthManager()
        
        # Переменные для 2FA
        self.temp_token = None
        self.setup_2fa_data = None
        
        # Создание интерфейса
        self.create_widgets()
        self.show_login_frame()
    
    def create_widgets(self):
        """Создание всех фреймов интерфейса"""
        
        # Главный контейнер
        self.main_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.main_frame.pack(fill="both", expand=True)
        
        # Логотип/Заголовок
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.pack(pady=30)
        
        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="🔐",
            font=("Segoe UI", 48)
        )
        self.logo_label.pack()
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="SecureAuth",
            font=("Segoe UI", 28, "bold"),
            text_color="white"
        )
        self.title_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Безопасная аутентификация",
            font=("Segoe UI", 14),
            text_color="#94A3B8"
        )
        self.subtitle_label.pack()
        
        # Контейнер для форм (переключаемый)
        self.forms_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.forms_container.pack(fill="both", expand=True, padx=40)
        
        # Создаем все фреймы форм
        self.login_frame = self.create_login_frame()
        self.register_frame = self.create_register_frame()
        self.twofa_frame = self.create_2fa_frame()
        self.twofa_setup_frame = self.create_2fa_setup_frame()
        self.dashboard_frame = self.create_dashboard_frame()
        
        # Футер
        self.footer_label = ctk.CTkLabel(
            self.main_frame,
            text="Защищено Argon2 + AES-256 + TOTP",
            font=("Segoe UI", 11),
            text_color="#64748B"
        )
        self.footer_label.pack(pady=20)
    
    def create_login_frame(self) -> ctk.CTkFrame:
        """Создание формы входа"""
        frame = ctk.CTkFrame(self.forms_container, fg_color=CARD_BG, corner_radius=16)
        
        # Заголовок
        ctk.CTkLabel(
            frame,
            text="Вход в систему",
            font=("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(pady=(30, 20))
        
        # Email
        ctk.CTkLabel(
            frame,
            text="Email",
            font=("Segoe UI", 13),
            text_color="#CBD5E1"
        ).pack(anchor="w", padx=30)
        
        self.login_email = ctk.CTkEntry(
            frame,
            placeholder_text="your@email.com",
            height=45,
            font=("Segoe UI", 13),
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A"
        )
        self.login_email.pack(fill="x", padx=30, pady=(5, 15))
        
        # Пароль
        ctk.CTkLabel(
            frame,
            text="Пароль",
            font=("Segoe UI", 13),
            text_color="#CBD5E1"
        ).pack(anchor="w", padx=30)
        
        self.login_password = ctk.CTkEntry(
            frame,
            placeholder_text="••••••••",
            height=45,
            font=("Segoe UI", 13),
            show="•",
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A"
        )
        self.login_password.pack(fill="x", padx=30, pady=(5, 10))
        
        # Показать пароль
        self.show_pass_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            frame,
            text="Показать пароль",
            variable=self.show_pass_var,
            command=self.toggle_login_password,
            font=("Segoe UI", 11),
            checkbox_height=18,
            checkbox_width=18
        ).pack(anchor="w", padx=30, pady=5)
        
        # Кнопка входа
        self.login_btn = ctk.CTkButton(
            frame,
            text="Войти",
            height=45,
            font=("Segoe UI", 14, "bold"),
            corner_radius=10,
            fg_color=THEME_COLOR,
            hover_color="#2563EB",
            command=self.handle_login
        )
        self.login_btn.pack(fill="x", padx=30, pady=(20, 15))
        
        # Разделитель
        ctk.CTkFrame(frame, height=1, fg_color="#334155").pack(fill="x", padx=30, pady=15)
        
        # Ссылка на регистрацию
        ctk.CTkLabel(
            frame,
            text="Нет аккаунта?",
            font=("Segoe UI", 13),
            text_color="#94A3B8"
        ).pack()
        
        ctk.CTkButton(
            frame,
            text="Создать аккаунт",
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent",
            hover_color="#334155",
            text_color=THEME_COLOR,
            command=self.show_register_frame
        ).pack(pady=5)
        
        return frame
    
    def create_register_frame(self) -> ctk.CTkFrame:
        """Создание формы регистрации"""
        frame = ctk.CTkFrame(self.forms_container, fg_color=CARD_BG, corner_radius=16)
        
        # Заголовок
        ctk.CTkLabel(
            frame,
            text="Создание аккаунта",
            font=("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(pady=(30, 20))
        
        # Email
        ctk.CTkLabel(
            frame,
            text="Email",
            font=("Segoe UI", 13),
            text_color="#CBD5E1"
        ).pack(anchor="w", padx=30)
        
        self.reg_email = ctk.CTkEntry(
            frame,
            placeholder_text="your@email.com",
            height=45,
            font=("Segoe UI", 13),
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A"
        )
        self.reg_email.pack(fill="x", padx=30, pady=(5, 15))
        
        # Пароль
        ctk.CTkLabel(
            frame,
            text="Пароль (мин. 12 символов)",
            font=("Segoe UI", 13),
            text_color="#CBD5E1"
        ).pack(anchor="w", padx=30)
        
        self.reg_password = ctk.CTkEntry(
            frame,
            placeholder_text="Создайте надёжный пароль",
            height=45,
            font=("Segoe UI", 13),
            show="•",
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A"
        )
        self.reg_password.pack(fill="x", padx=30, pady=(5, 5))
        
        # Индикатор сложности пароля
        self.password_strength = ctk.CTkProgressBar(
            frame,
            height=4,
            corner_radius=2,
            fg_color="#0F172A",
            progress_color=ERROR_COLOR
        )
        self.password_strength.pack(fill="x", padx=30, pady=(0, 5))
        self.password_strength.set(0)
        
        self.password_hint = ctk.CTkLabel(
            frame,
            text="Минимум 12 символов, заглавная, строчная, цифра, спецсимвол",
            font=("Segoe UI", 10),
            text_color="#64748B"
        )
        self.password_hint.pack(anchor="w", padx=30)
        
        # Подтверждение пароля
        ctk.CTkLabel(
            frame,
            text="Подтвердите пароль",
            font=("Segoe UI", 13),
            text_color="#CBD5E1"
        ).pack(anchor="w", padx=30, pady=(15, 0))
        
        self.reg_password_confirm = ctk.CTkEntry(
            frame,
            placeholder_text="Повторите пароль",
            height=45,
            font=("Segoe UI", 13),
            show="•",
            corner_radius=10,
            border_color="#334155",
            fg_color="#0F172A"
        )
        self.reg_password_confirm.pack(fill="x", padx=30, pady=(5, 15))
        
        # Отслеживание изменения пароля для индикатора
        self.reg_password.bind('<KeyRelease>', self.check_password_strength)
        
        # Кнопка регистрации
        self.reg_btn = ctk.CTkButton(
            frame,
            text="Зарегистрироваться",
            height=45,
            font=("Segoe UI", 14, "bold"),
            corner_radius=10,
            fg_color=SUCCESS_COLOR,
            hover_color="#059669",
            command=self.handle_register
        )
        self.reg_btn.pack(fill="x", padx=30, pady=(20, 15))
        
        # Разделитель
        ctk.CTkFrame(frame, height=1, fg_color="#334155").pack(fill="x", padx=30, pady=15)
        
        # Ссылка на вход
        ctk.CTkLabel(
            frame,
            text="Уже есть аккаунт?",
            font=("Segoe UI", 13),
            text_color="#94A3B8"
        ).pack()
        
        ctk.CTkButton(
            frame,
            text="Войти",
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent",
            hover_color="#334155",
            text_color=THEME_COLOR,
            command=self.show_login_frame
        ).pack(pady=5)
        
        return frame
    
    def create_2fa_frame(self) -> ctk.CTkFrame:
        """Создание формы ввода 2FA кода"""
        frame = ctk.CTkFrame(self.forms_container, fg_color=CARD_BG, corner_radius=16)
        
        ctk.CTkLabel(
            frame,
            text="🔐 Двухфакторная аутентификация",
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        ).pack(pady=(40, 20))
        
        ctk.CTkLabel(
            frame,
            text="Введите 6-значный код из приложения-аутентификатора",
            font=("Segoe UI", 13),
            text_color="#94A3B8",
            wraplength=350
        ).pack(pady=(0, 30))
        
        # Поле для кода
        self.twofa_code = ctk.CTkEntry(
            frame,
            placeholder_text="000000",
            height=50,
            width=200,
            font=("Segoe UI", 24, "bold"),
            justify="center",
            corner_radius=12,
            border_color=THEME_COLOR,
            fg_color="#0F172A",
            border_width=2
        )
        self.twofa_code.pack(pady=20)
        self.twofa_code.bind('<KeyRelease>', self.format_2fa_code)
        
        # Кнопка подтверждения
        self.twofa_btn = ctk.CTkButton(
            frame,
            text="Подтвердить",
            height=45,
            width=200,
            font=("Segoe UI", 14, "bold"),
            corner_radius=10,
            fg_color=THEME_COLOR,
            command=self.handle_2fa_verify
        )
        self.twofa_btn.pack(pady=20)
        
        # Резервный код
        ctk.CTkButton(
            frame,
            text="Использовать резервный код",
            font=("Segoe UI", 12),
            fg_color="transparent",
            hover_color="#334155",
            text_color="#94A3B8",
            command=self.use_backup_code
        ).pack(pady=10)
        
        # Отмена
        ctk.CTkButton(
            frame,
            text="← Назад к входу",
            font=("Segoe UI", 12),
            fg_color="transparent",
            hover_color="#334155",
            text_color="#94A3B8",
            command=self.cancel_2fa
        ).pack(pady=20)
        
        return frame
    
    def create_2fa_setup_frame(self) -> ctk.CTkFrame:
        """Создание формы настройки 2FA"""
        frame = ctk.CTkFrame(self.forms_container, fg_color=CARD_BG, corner_radius=16)
        
        ctk.CTkLabel(
            frame,
            text="Настройка 2FA",
            font=("Segoe UI", 20, "bold"),
            text_color="white"
        ).pack(pady=(30, 10))
        
        ctk.CTkLabel(
            frame,
            text="Отсканируйте QR-код в Google Authenticator",
            font=("Segoe UI", 13),
            text_color="#94A3B8"
        ).pack()
        
        # Контейнер для QR-кода
        self.qr_container = ctk.CTkFrame(frame, fg_color="white", width=200, height=200)
        self.qr_container.pack(pady=20)
        self.qr_container.pack_propagate(False)
        
        self.qr_label = ctk.CTkLabel(self.qr_container, text="")
        self.qr_label.pack(expand=True)
        
        # Секрет для ручного ввода
        self.secret_frame = ctk.CTkFrame(frame, fg_color="#0F172A", corner_radius=8)
        self.secret_frame.pack(fill="x", padx=40, pady=10)
        
        self.secret_label = ctk.CTkLabel(
            self.secret_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            text_color=THEME_COLOR
        )
        self.secret_label.pack(pady=10)
        
        ctk.CTkButton(
            self.secret_frame,
            text="Копировать секрет",
            font=("Segoe UI", 11),
            fg_color="#334155",
            hover_color="#475569",
            command=self.copy_secret
        ).pack(pady=(0, 10))
        
        # Резервные коды (скрыты по умолчанию)
        self.backup_frame = ctk.CTkFrame(frame, fg_color="#0F172A", corner_radius=8)
        self.backup_frame.pack(fill="x", padx=40, pady=10)
        self.backup_frame.pack_forget()  # Скрыть
        
        ctk.CTkLabel(
            self.backup_frame,
            text="Сохраните резервные коды!",
            font=("Segoe UI", 13, "bold"),
            text_color=ERROR_COLOR
        ).pack(pady=10)
        
        self.backup_codes_text = ctk.CTkTextbox(
            self.backup_frame,
            height=100,
            font=("Segoe UI", 11, "bold"),
            fg_color="#0F172A",
            text_color=SUCCESS_COLOR
        )
        self.backup_codes_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Верификация
        ctk.CTkLabel(
            frame,
            text="Введите код из приложения для подтверждения:",
            font=("Segoe UI", 13),
            text_color="#CBD5E1"
        ).pack(pady=(20, 5))
        
        self.setup_code = ctk.CTkEntry(
            frame,
            placeholder_text="000000",
            height=45,
            width=150,
            font=("Segoe UI", 18, "bold"),
            justify="center",
            corner_radius=10
        )
        self.setup_code.pack(pady=10)
        
        ctk.CTkButton(
            frame,
            text="Включить 2FA",
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=SUCCESS_COLOR,
            hover_color="#059669",
            command=self.handle_setup_verify
        ).pack(pady=20)
        
        ctk.CTkButton(
            frame,
            text="Пропустить (не рекомендуется)",
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color="#64748B",
            hover_color="#334155",
            command=self.skip_2fa_setup
        ).pack(pady=10)
        
        return frame
    
    def create_dashboard_frame(self) -> ctk.CTkFrame:
        """Создание личного кабинета"""
        frame = ctk.CTkFrame(self.forms_container, fg_color=CARD_BG, corner_radius=16)
        
        # Приветствие
        self.welcome_label = ctk.CTkLabel(
            frame,
            text="Добро пожаловать!",
            font=("Segoe UI", 22, "bold"),
            text_color="white"
        )
        self.welcome_label.pack(pady=(40, 10))
        
        self.user_email_label = ctk.CTkLabel(
            frame,
            text="",
            font=("Segoe UI", 14),
            text_color="#94A3B8"
        )
        self.user_email_label.pack()
        
        # Статус безопасности
        self.security_frame = ctk.CTkFrame(frame, fg_color="#0F172A", corner_radius=12)
        self.security_frame.pack(fill="x", padx=40, pady=30)
        
        self.security_status = ctk.CTkLabel(
            self.security_frame,
            text="🔒 Защита: Стандартная",
            font=("Segoe UI", 14, "bold"),
            text_color="#FBBF24"
        )
        self.security_status.pack(pady=15)
        
        # Кнопка включения 2FA
        self.enable_2fa_btn = ctk.CTkButton(
            self.security_frame,
            text="Включить 2FA",
            font=("Segoe UI", 13, "bold"),
            fg_color=THEME_COLOR,
            command=self.start_2fa_setup
        )
        self.enable_2fa_btn.pack(pady=(0, 15))
        
        # Инфо
        ctk.CTkLabel(
            frame,
            text="Ваши данные защищены:",
            font=("Segoe UI", 13, "bold"),
            text_color="white"
        ).pack(anchor="w", padx=40, pady=(20, 10))
        
        protections = [
            "✓ Пароль: Argon2id хеширование",
            "✓ Сессия: JWT с коротким сроком жизни",
            "✓ Шифрование: AES-256 для чувствительных данных"
        ]
        
        for protection in protections:
            ctk.CTkLabel(
                frame,
                text=protection,
                font=("Segoe UI", 12),
                text_color="#94A3B8"
            ).pack(anchor="w", padx=40)
        
        # Кнопка выхода
        ctk.CTkButton(
            frame,
            text="Выйти из аккаунта",
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=ERROR_COLOR,
            hover_color="#DC2626",
            command=self.handle_logout
        ).pack(fill="x", padx=40, pady=(40, 20))
        
        return frame
    
    # ===== МЕТОДЫ ПЕРЕКЛЮЧЕНИЯ ФРЕЙМОВ =====
    
    def hide_all_frames(self):
        """Скрыть все формы"""
        for frame in [self.login_frame, self.register_frame, self.twofa_frame, 
                      self.twofa_setup_frame, self.dashboard_frame]:
            frame.pack_forget()
    
    def show_login_frame(self):
        """Показать форму входа"""
        self.hide_all_frames()
        self.login_frame.pack(fill="both", expand=True, padx=40, pady=20)
        self.login_email.focus()
    
    def show_register_frame(self):
        """Показать форму регистрации"""
        self.hide_all_frames()
        self.register_frame.pack(fill="both", expand=True, padx=40, pady=20)
        self.reg_email.focus()
    
    def show_2fa_frame(self):
        """Показать форму 2FA"""
        self.hide_all_frames()
        self.twofa_frame.pack(fill="both", expand=True, padx=40, pady=20)
        self.twofa_code.focus()
    
    def show_2fa_setup_frame(self):
        """Показать настройку 2FA"""
        self.hide_all_frames()
        self.twofa_setup_frame.pack(fill="both", expand=True, padx=40, pady=20)
    
    def show_dashboard(self):
        """Показать личный кабинет"""
        self.hide_all_frames()
        
        # Обновить данные пользователя
        if self.auth.current_user:
            self.welcome_label.configure(
                text=f"Привет, {self.auth.current_user['email'].split('@')[0]}!"
            )
            self.user_email_label.configure(text=self.auth.current_user['email'])
            
            # Обновить статус 2FA
            if self.auth.current_user.get('totp_enabled'):
                self.security_status.configure(
                    text="🔐 Защита: Максимальная (2FA включена)",
                    text_color=SUCCESS_COLOR
                )
                self.enable_2fa_btn.pack_forget()
            else:
                self.security_status.configure(
                    text="🔒 Защита: Стандартная (рекомендуется 2FA)",
                    text_color="#FBBF24"
                )
                self.enable_2fa_btn.pack(pady=(0, 15))
        
        self.dashboard_frame.pack(fill="both", expand=True, padx=40, pady=20)
    
    # ===== ОБРАБОТЧИКИ СОБЫТИЙ =====
    
    def toggle_login_password(self):
        """Переключить видимость пароля"""
        if self.show_pass_var.get():
            self.login_password.configure(show="")
        else:
            self.login_password.configure(show="•")
    
    def check_password_strength(self, event=None):
        """Проверка сложности пароля"""
        password = self.reg_password.get()
        score = 0
        
        if len(password) >= 12:
            score += 0.25
        if any(c.isupper() for c in password):
            score += 0.25
        if any(c.islower() for c in password):
            score += 0.25
        if any(c.isdigit() for c in password):
            score += 0.125
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 0.125
        
        self.password_strength.set(score)
        
        # Цвет индикатора
        if score < 0.4:
            self.password_strength.configure(progress_color=ERROR_COLOR)
        elif score < 0.8:
            self.password_strength.configure(progress_color="#FBBF24")
        else:
            self.password_strength.configure(progress_color=SUCCESS_COLOR)
    
    def format_2fa_code(self, event=None):
        """Форматирование кода 2FA (только цифры)"""
        code = self.twofa_code.get()
        # Удалить всё кроме цифр
        digits = ''.join(filter(str.isdigit, code))
        # Ограничить 6 цифрами
        self.twofa_code.delete(0, 'end')
        self.twofa_code.insert(0, digits[:6])
    
    def handle_login(self):
        """Обработка входа"""
        email = self.login_email.get().strip()
        password = self.login_password.get()
        
        if not email or not password:
            self.show_error("Заполните все поля")
            return
        
        # Показать загрузку
        self.login_btn.configure(text="Вход...", state="disabled")
        self.update()
        
        success, message, data = self.auth.login(email, password)
        
        self.login_btn.configure(text="Войти", state="normal")
        
        if success:
            if message == "requires_2fa":
                self.temp_token = data["temp_token"]
                self.show_2fa_frame()
            else:
                self.show_dashboard()
        else:
            self.show_error(message)
    
    def handle_2fa_verify(self):
        """Проверка кода 2FA"""
        code = self.twofa_code.get()
        
        if len(code) != 6:
            self.show_error("Введите 6-значный код")
            return
        
        self.twofa_btn.configure(text="Проверка...", state="disabled")
        self.update()
        
        success, message = self.auth.verify_2fa(code, self.temp_token)
        
        self.twofa_btn.configure(text="Подтвердить", state="normal")
        
        if success:
            self.show_dashboard()
        else:
            self.show_error(message)
    
    def use_backup_code(self):
        """Использование резервного кода"""
        # Просто позволяем ввести резервный код в то же поле
        self.twofa_code.configure(placeholder_text="XXXX-XXXX-XXXX")
        self.twofa_code.delete(0, 'end')
    
    def cancel_2fa(self):
        """Отмена 2FA и возврат к логину"""
        self.temp_token = None
        self.twofa_code.delete(0, 'end')
        self.show_login_frame()
    
    def handle_register(self):
        """Обработка регистрации"""
        email = self.reg_email.get().strip()
        password = self.reg_password.get()
        confirm = self.reg_password_confirm.get()
        
        # Валидация
        if not email or not password:
            self.show_error("Заполните все поля")
            return
        
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            self.show_error("Введите корректный email")
            return
        
        if password != confirm:
            self.show_error("Пароли не совпадают")
            return
        
        # Проверка сложности
        is_strong, msg = self._check_password_rules(password)
        if not is_strong:
            self.show_error(msg)
            return
        
        # Показать загрузку
        self.reg_btn.configure(text="Создание...", state="disabled")
        self.update()
        
        success, message = self.auth.register(email, password)
        
        self.reg_btn.configure(text="Зарегистрироваться", state="normal")
        
        if success:
            self.show_success(message)
            # Очистить поля и перейти к логину
            self.reg_email.delete(0, 'end')
            self.reg_password.delete(0, 'end')
            self.reg_password_confirm.delete(0, 'end')
            self.login_email.insert(0, email)
            self.after(1500, self.show_login_frame)
        else:
            self.show_error(message)
    
    def _check_password_rules(self, password: str) -> tuple[bool, str]:
        """Проверка правил пароля"""
        if len(password) < 12:
            return False, "Пароль должен быть минимум 12 символов"
        if not any(c.isupper() for c in password):
            return False, "Добавьте заглавную букву"
        if not any(c.islower() for c in password):
            return False, "Добавьте строчную букву"
        if not any(c.isdigit() for c in password):
            return False, "Добавьте цифру"
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Добавьте спецсимвол (!@#$...)"
        return True, "OK"
    
    def start_2fa_setup(self):
        """Начало настройки 2FA"""
        success, data = self.auth.setup_2fa()
        
        if not success:
            self.show_error(data.get("error", "Ошибка настройки 2FA"))
            return
        
        self.setup_2fa_data = data
        
        # Отобразить QR-код
        qr_base64 = data.get("qr_code", "")
        if qr_base64:
            try:
                qr_image = Image.open(io.BytesIO(base64.b64decode(qr_base64)))
                qr_image = qr_image.resize((180, 180), Image.Resampling.LANCZOS)
                qr_photo = ImageTk.PhotoImage(qr_image)
                self.qr_label.configure(image=qr_photo)
                self.qr_label.image = qr_photo  # Сохранить ссылку
            except Exception as e:
                print(f"Error loading QR: {e}")
        
        # Показать секрет
        secret = data.get("secret", "")
        # Форматировать секрет: XXXX XXXX XXXX XXXX
        formatted = ' '.join(secret[i:i+4] for i in range(0, len(secret), 4))
        self.secret_label.configure(text=formatted)
        
        # Сохранить резервные коды (показать после успешной настройки)
        backup_codes = data.get("backup_codes", [])
        self.backup_codes_text.delete("0.0", "end")
        self.backup_codes_text.insert("0.0", "\n".join(backup_codes))
        
        self.show_2fa_setup_frame()
    
    def copy_secret(self):
        """Копирование секрета в буфер обмена"""
        if self.setup_2fa_data:
            secret = self.setup_2fa_data.get("secret", "")
            self.clipboard_clear()
            self.clipboard_append(secret)
            self.show_success("Секрет скопирован!")
    
    def handle_setup_verify(self):
        """Подтверждение настройки 2FA"""
        code = self.setup_code.get()
        
        if len(code) != 6:
            self.show_error("Введите 6-значный код")
            return
        
        success, message = self.auth.verify_2fa_setup(code)
        
        if success:
            # Показать резервные коды
            self.backup_frame.pack(fill="x", padx=40, pady=10)
            self.show_success("2FA успешно включена! Сохраните резервные коды.")
            self.after(3000, self.show_dashboard)
        else:
            self.show_error(message)
    
    def skip_2fa_setup(self):
        """Пропуск настройки 2FA"""
        self.show_dashboard()
    
    def handle_logout(self):
        """Выход из аккаунта"""
        self.auth.logout()
        self.login_email.delete(0, 'end')
        self.login_password.delete(0, 'end')
        self.show_login_frame()
        self.show_success("Вы вышли из системы")
    
    def show_error(self, message: str):
        """Показать ошибку"""
        messagebox.showerror("Ошибка", message)
    
    def show_success(self, message: str):
        """Показать успешное сообщение"""
        messagebox.showinfo("Успех", message)


def main():
    """Точка входа"""
    # Установка DPI awareness для чёткого отображения на Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = ModernAuthApp()
    app.mainloop()


if __name__ == "__main__":
    main()