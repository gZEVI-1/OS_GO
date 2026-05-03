import sys
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                QLabel, QComboBox, QPushButton)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from windows.app_settings import AppSettings, Language, Theme


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = AppSettings()
        self.setup_ui()
        self.load_current_settings()
        self.apply_theme()
        
        # Подписываемся на изменения настроек для обновления UI
        self.settings.settings_changed.connect(self.on_settings_changed)
    
    def setup_ui(self):
        self.setWindowTitle(self.settings.get_text("settings_title"))
        self.setModal(True)
        self.setFixedSize(400, 320)
        self.setMinimumSize(400, 320)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Выбор языка
        language_layout = QHBoxLayout()
        self.language_label = QLabel(self.settings.get_text("language_label"))
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.settings.get_text("language_english"), Language.ENGLISH)
        self.language_combo.addItem(self.settings.get_text("language_russian"), Language.RUSSIAN)
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_combo)
        layout.addLayout(language_layout)
        
        # Выбор темы
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(self.settings.get_text("theme_label"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.settings.get_text("theme_dark"), Theme.DARK)
        self.theme_combo.addItem(self.settings.get_text("theme_light"), Theme.LIGHT)
        self.theme_combo.addItem(self.settings.get_text("theme_blue"), Theme.ASIA)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        layout.addStretch()
        
        # Кнопка GitHub
        self.github_button = QPushButton(self.settings.get_text("github_link"))
        self.github_button.setStyleSheet("""
            QPushButton {
                background-color: #24292e;
                color: white;
                border: none;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0366d6;
            }
        """)
        self.github_button.clicked.connect(self.open_github)
        layout.addWidget(self.github_button)
        
        # Кнопка закрытия
        self.close_button = QPushButton(self.settings.get_text("close_button"))
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
        
        # Подключаем сигналы
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
    
    def load_current_settings(self):
        """Загружает текущие настройки в комбобоксы"""
        index = self.language_combo.findData(self.settings.language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        index = self.theme_combo.findData(self.settings.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
    
    def on_language_changed(self):
        """Обработчик изменения языка"""
        new_language = self.language_combo.currentData()
        if new_language and new_language != self.settings.language:
            self.settings.language = new_language
    
    def on_theme_changed(self):
        """Обработчик изменения темы"""
        new_theme = self.theme_combo.currentData()
        if new_theme and new_theme != self.settings.theme:
            self.settings.theme = new_theme
    
    def on_settings_changed(self):
        """Обновляет UI при изменении настроек"""
        # Блокируем сигналы, чтобы не вызывать рекурсию
        self.language_combo.blockSignals(True)
        self.theme_combo.blockSignals(True)
        # Обновляем заголовок
        self.setWindowTitle(self.settings.get_text("settings_title"))
        
        # Обновляем тексты меток
        self.language_label.setText(self.settings.get_text("language_label"))
        self.theme_label.setText(self.settings.get_text("theme_label"))
        self.github_button.setText(self.settings.get_text("github_link"))
        self.close_button.setText(self.settings.get_text("close_button"))
        
        # Сохраняем текущие значения
        current_lang = self.language_combo.currentData()
        current_theme = self.theme_combo.currentData()
        
        # Пересоздаем комбобоксы с новыми текстами
        self.language_combo.clear()
        self.language_combo.addItem(self.settings.get_text("language_english"), Language.ENGLISH)
        self.language_combo.addItem(self.settings.get_text("language_russian"), Language.RUSSIAN)
        
        self.theme_combo.clear()
        self.theme_combo.addItem(self.settings.get_text("theme_dark"), Theme.DARK)
        self.theme_combo.addItem(self.settings.get_text("theme_light"), Theme.LIGHT)
        self.theme_combo.addItem(self.settings.get_text("theme_blue"), Theme.ASIA)
        
        # Восстанавливаем выбранные значения
        self.language_combo.setCurrentIndex(self.language_combo.findData(current_lang))
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(current_theme))
        
        # Разблокируем сигналы
        self.language_combo.blockSignals(False)
        self.theme_combo.blockSignals(False)
        
        # Применяем новую тему
        self.apply_theme()
    
    def apply_theme(self):
        #тема к диалогу
        self.setStyleSheet(self.settings.get_theme_stylesheet())
    
    def open_github(self):
        QDesktopServices.openUrl(QUrl("https://github.com/gZEVI-1/OS_GO/invitations"))