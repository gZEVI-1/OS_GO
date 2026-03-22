import os
from PySide6.QtWidgets import QDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
# from generated.ui_profile_window import Ui_profile_window
import sys
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(root_path / "interface" / "Go_app" ))
from generated.ui_profile_window import Ui_profile_window

class ProfileWindow(QDialog):
    """Всплывающее окно профиля игрока"""
    
    def __init__(self, player_data, parent=None):
        super().__init__(parent)
        
        # Загружаем интерфейс
        self.ui = Ui_profile_window()
        self.ui.setupUi(self)
        
        # Делаем окно модальным и плавающим
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        
        # Заполняем данными
        self.update_profile(player_data)
        
        # Подключаем кнопку закрытия
        self.ui.buttonClose.clicked.connect(self.close)
    
    def update_profile(self, player_data):
        """Обновляет информацию в профиле"""
        self.ui.nameLabel.setText(f"Имя: {player_data.get('name', 'Неизвестно')}")
        self.ui.ratingLabel.setText(f"Рейтинг: {player_data.get('rating', 0)}")
        self.ui.winsLabel.setText(f"Побед: {player_data.get('wins', 0)}")
        self.ui.lossesLabel.setText(f"Поражений: {player_data.get('losses', 0)}")
        self.ui.countryLabel.setText(f"Страна: {player_data.get('country', 'Не указана')}")
        
        # Загрузка аватара
        avatar_path = player_data.get('avatar_path')
        if avatar_path and isinstance(avatar_path, str) and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(100, 100, 
                                             Qt.KeepAspectRatioByExpanding,
                                             Qt.SmoothTransformation)
                self.ui.avatarLabel.setPixmap(scaled_pixmap)
                self.ui.avatarLabel.setAlignment(Qt.AlignCenter)
            else:
                self.ui.avatarLabel.setText("❌ Ошибка")
                self.ui.avatarLabel.setAlignment(Qt.AlignCenter)
        else:
            # Заглушка
            self.ui.avatarLabel.setText("👤")
            self.ui.avatarLabel.setAlignment(Qt.AlignCenter)
            self.ui.avatarLabel.setStyleSheet("font-size: 40px; color: gray;")