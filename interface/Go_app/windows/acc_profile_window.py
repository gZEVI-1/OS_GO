# profile_window.py
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Signal
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.main_profile import Ui_ProfileWindow

class ProfileWindow(QDialog):
    """Окно профиля пользователя"""
    
    profile_updated = Signal(dict)
    
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.ui = Ui_ProfileWindow()
        self.ui.setupUi(self)
        
        self.user_data = user_data
        
        self.setup_ui()
        self.connect_signals()
        
        self.setModal(True)
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Устанавливаем данные пользователя
        self.ui.userNameLabel.setText(self.user_data.get('full_name', self.user_data.get('email', 'Пользователь')))
        self.ui.emailLabel.setText(self.user_data.get('email', ''))
        
        # Аватар по умолчанию (эмодзи)
        self.ui.avatarButton.setText("👤")
    
    def connect_signals(self):
        """Подключает сигналы"""
        self.ui.statsButton.clicked.connect(self.on_stats_click)
        self.ui.editProfileButton.clicked.connect(self.on_edit_profile_click)
    
    def on_stats_click(self):
        """Открывает окно статистики"""
        QMessageBox.information(
            self,
            "Статистика",
            f"Игр сыграно: 0\nПобед: 0\nПоражений: 0\nРейтинг: 1000"
        )
    
    def on_edit_profile_click(self):
        """Открывает окно редактирования профиля"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование профиля")
        dialog.setModal(True)
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        name_edit = QLineEdit(self.user_data.get('full_name', ''))
        name_edit.setPlaceholderText("Имя пользователя")
        form_layout.addRow("Имя:", name_edit)
        
        layout.addLayout(form_layout)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self.save_profile(name_edit.text(), dialog))
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        
        dialog.exec()
    
    def save_profile(self, new_name, dialog):
        """Сохраняет изменения профиля"""
        if new_name and new_name != self.user_data.get('full_name', ''):
            self.user_data['full_name'] = new_name
            self.ui.userNameLabel.setText(new_name)
            self.profile_updated.emit(self.user_data)
            QMessageBox.information(self, "Успех", "Профиль обновлен")
        dialog.accept()