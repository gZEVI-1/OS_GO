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
    # Глобальные настройки приложения
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
            self._theme = Theme.ASIA  # По умолчанию ASIA
            self._settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
            
            # ЦВЕТА (обязательно должны быть!)
            self.theme_colors = {
                Theme.DARK: {
                    "bg_primary": "#1C1A17",
                    "bg_secondary": "#2A2723",
                    "text_primary": "#F0E9E0",
                    "text_secondary": "#A39E99",
                    "button_bg": "#4A4540",
                    "button_hover": "#2D2A27",
                    "button_text": "#F0E9E0",
                    "border": "#2A2723",
                    "accent": "#4A4540",
                },
                Theme.LIGHT: {
                    "bg_primary": "#F7F3EB",
                    "bg_secondary": "#F7F3EB",
                    "text_primary": "#3A322B",
                    "text_secondary": "#534941",
                    "button_bg": "#8F8A84",
                    "button_hover": "#68635D",
                    "button_text": "#3A322B",
                    "border": "#E8E0D3",
                    "accent": "#463F39",
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
            print(f"Тема изменена на: {self._theme.value}")
            self.settings_changed.emit()        

    def get_color(self, color_name):
        return self.theme_colors.get(self._theme, {}).get(color_name, "#000000")
    
    def get_theme_stylesheet(self):
        """Старый метод - для совместимости"""
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
            "language_english": {
                Language.ENGLISH: "English",
                Language.RUSSIAN: "Английский"
            },
            "language_russian": {
                Language.ENGLISH: "Russian",
                Language.RUSSIAN: "Русский"
            },
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
    
    # ========== ГЛАВНЫЙ МЕТОД - ЗАГРУЗКА QSS ФАЙЛОВ ==========
    def get_stylesheet(self):
        """Загружает QSS файл для текущей темы"""
        
        # Определяем имя файла по теме
        theme_files = {
            Theme.DARK: "dark.qss",
            Theme.LIGHT: "light.qss",
            Theme.ASIA: "asia.qss"
        }
        
        theme_file = theme_files.get(self._theme, "dark.qss")
        
        # Путь к папке themes (на уровень выше windows)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(base_dir, "themes", theme_file)
        
        print(f"Загрузка темы: {self._theme.value}")
        print(f"Путь к QSS: {qss_path}")
        
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"✓ QSS файл загружен, размер: {len(content)} символов")
                    return content
            except Exception as e:
                print(f"✗ Ошибка чтения QSS: {e}")
        else:
            print(f"✗ QSS файл не найден: {qss_path}")
            # Покажем содержимое папки themes для отладки
            themes_dir = os.path.dirname(qss_path)
            if os.path.exists(themes_dir):
                print(f"Содержимое папки themes: {os.listdir(themes_dir)}")
        
        # Если QSS файл не найден, используем встроенные стили
        print("→ Использую встроенные стили (get_theme_stylesheet)")
        return self.get_theme_stylesheet()
    
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
                    elif theme_value == "asia":
                        self._theme = Theme.ASIA
                        
            except Exception as e:
                print(f"Error loading settings: {e}")