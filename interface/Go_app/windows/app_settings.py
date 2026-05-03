import json
import os
from PySide6.QtCore import QObject, Signal
from enum import Enum

class Language(Enum):
    RUSSIAN = "ru"
    ENGLISH = "en"

class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"
    ASIA = "asia"

class AppSettings(QObject):
    #Глобальные настройки приложения
    settings_changed = Signal()
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance    
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            self._language = Language.ENGLISH
            self._theme = Theme.DARK
            self._settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
            self._updating = False
            
            # ЦВЕТА
            self.theme_colors = {
                Theme.DARK: {
                    "bg_primary": "#1C1A17",      # Основной фон
                    "bg_secondary": "#2A2723",    # Вторичный фон
                    "text_primary": "#F0E9E0",    # Основной текст
                    "text_secondary": "#A39E99",  # Вторичный текст
                    "button_bg": "#4A4540",       # Фон кнопки
                    "button_hover": "#2D2A27",    # Кнопка при наведении
                    "button_text": "#F0E9E0",     # Текст на кнопке
                    "border": "#2A2723",          # Цвет границ
                    "accent": "#4A4540",          # Акцентный цвет
                },
                Theme.LIGHT: {
                    "bg_primary": "#f5f5f5",
                    "bg_secondary": "#ffffff",
                    "text_primary": "#000000",
                    "text_secondary": "#666666",
                    "button_bg": "#4CAF50",
                    "button_hover": "#45a049",
                    "button_text": "#ffffff",
                    "border": "#cccccc",
                    "accent": "#4CAF50",
                },
                Theme.ASIA: {
                    "bg_primary": "#1a237e",
                    "bg_secondary": "#283593",
                    "text_primary": "#ffffff",
                    "text_secondary": "#e0e0e0",
                    "button_bg": "#00bcd4",
                    "button_hover": "#00acc1",
                    "button_text": "#000000",
                    "border": "#3949ab",
                    "accent": "#00bcd4",
                },
            }
            
            self.load_settings() 

    @property
    def language(self):
        return self._language
    
    @language.setter
    def language(self, value):
        if isinstance(value, Language) and value != self._language:
            self._language = value
            self.save_settings()
            self.settings_changed.emit()

    @property
    def theme(self):
        return self._theme
    
    @theme.setter
    def theme(self, value):
        if isinstance(value, Theme) and value != self._theme:
            self._theme = value
            self.save_settings()
            self.settings_changed.emit()        

    def get_color(self, color_name):
        return self.theme_colors.get(self._theme, {}).get(color_name, "#000000")
    
    def get_theme_stylesheet(self):
        colors = self.theme_colors.get(self._theme, self.theme_colors[Theme.DARK])
        
        return f"""
            QWidget {{
                background-color: {colors["bg_primary"]};
                color: {colors["text_primary"]};
            }}
            QPushButton {{
                background-color: {colors["button_bg"]};
                color: {colors["button_text"]};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
            }}
            QPushButton:disabled {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_secondary"]};
            }}
            QLabel {{
                color: {colors["text_primary"]};
            }}
            QLineEdit, QTextEdit {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_primary"]};
                border: 1px solid {colors["border"]};
                border-radius: 3px;
                padding: 5px;
            }}
            QDialog {{
                background-color: {colors["bg_primary"]};
            }}
            QMenuBar {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_primary"]};
            }}
            QMenuBar::item:selected {{
                background-color: {colors["button_hover"]};
            }}
            QListWidget {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_primary"]};
                border: 1px solid {colors["border"]};
            }}
            QListWidget::item:selected {{
                background-color: {colors["button_bg"]};
            }}
        """           
    def get_text(self, key):
        texts = {
            "settings_title": {
                Language.ENGLISH: "Settings",
                Language.RUSSIAN: "Настройки"
            },
            "language_label": {
                Language.ENGLISH: "Language:",
                Language.RUSSIAN: "Язык:"
            },
            "theme_label": {
                Language.ENGLISH: "Theme:",
                Language.RUSSIAN: "Тема:"
            },
            "github_link": {
                Language.ENGLISH: "GitHub Repository",
                Language.RUSSIAN: "Репозиторий GitHub"
            },
            "close_button": {
                Language.ENGLISH: "Close",
                Language.RUSSIAN: "Закрыть"
            },
            
            # Языки
            "language_english": {
                Language.ENGLISH: "English",
                Language.RUSSIAN: "Английский"
            },
            "language_russian": {
                Language.ENGLISH: "Russian",
                Language.RUSSIAN: "Русский"
            },
            
            # Темы
            "theme_dark": {
                Language.ENGLISH: "Dark",
                Language.RUSSIAN: "Темная"
            },
            "theme_light": {
                Language.ENGLISH: "Light",
                Language.RUSSIAN: "Светлая"
            },
            "theme_blue": {
                Language.ENGLISH: "Asia",
                Language.RUSSIAN: "Азия"
            },
            
            # Окно игры
            "game_title": {
                Language.ENGLISH: "Go Game",
                Language.RUSSIAN: "Игра Го"
            },
            "pass_button": {
                Language.ENGLISH: "Pass",
                Language.RUSSIAN: "Пас"
            },
            "resign_button": {
                Language.ENGLISH: "Resign",
                Language.RUSSIAN: "Сдаться"
            },
            "resign_title": {
                Language.ENGLISH: "Resign",
                Language.RUSSIAN: "Сдаться"
            },
            "resign_confirm": {
                Language.ENGLISH: "Are you sure you want to resign?",
                Language.RUSSIAN: "Вы уверены, что хотите сдаться?"
            },
            "game_ended": {
                Language.ENGLISH: "Game Over",
                Language.RUSSIAN: "Игра окончена"
            },
            "opponent_won": {
                Language.ENGLISH: "You resigned. Opponent wins!",
                Language.RUSSIAN: "Вы сдались. Победил противник!"
            },
            "black": {
                Language.ENGLISH: "Black",
                Language.RUSSIAN: "Черные"
            },
            "white": {
                Language.ENGLISH: "White",
                Language.RUSSIAN: "Белые"
            },
            
            # Главное меню
            "open_online": {
                Language.ENGLISH: "Online Game",
                Language.RUSSIAN: "Онлайн игра"
            },
            "open_offline": {
                Language.ENGLISH: "Offline Game",
                Language.RUSSIAN: "Оффлайн игра"
            },
            "open_bot": {
                Language.ENGLISH: "Bot Game",
                Language.RUSSIAN: "Игра с ботом"
            },
            "open_instruction": {
                Language.ENGLISH: "Rules",
                Language.RUSSIAN: "Правила"
            },
            "open_account": {
                Language.ENGLISH: "Account",
                Language.RUSSIAN: "Аккаунт"
            },
        }
        return texts.get(key, {}).get(self._language, key)
    
    def save_settings(self):
        settings_data = {
            "language": self._language.value,
            "theme": self._theme.value
        }
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                if "language" in settings_data:
                    lang_value = settings_data["language"]
                    if lang_value == "ru":
                        self._language = Language.RUSSIAN
                    elif lang_value == "en":
                        self._language = Language.ENGLISH
                
                if "theme" in settings_data:
                    theme_value = settings_data["theme"]
                    if theme_value == "light":
                        self._theme = Theme.LIGHT
                    elif theme_value == "dark":
                        self._theme = Theme.DARK
                    elif theme_value == "blue":
                        self._theme = Theme.BLUE
                        
            except Exception as e:
                print(f"Error loading settings: {e}")