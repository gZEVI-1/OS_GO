from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject
from windows.app_settings import AppSettings

class BaseWindow(QWidget):
    """
    Базовый класс для всех окон приложения.
    Содержит общую логику и доступ к навигации и настройкам.
    """
    
    def __init__(self, navigation, parent=None):
        super().__init__(parent)
        self.navigation = navigation
        self.settings = AppSettings()  # Глобальные настройки
        
        self.settings.settings_changed.connect(self.on_settings_changed)
        
        # Применяем текущую тему
        self.apply_theme()
    
    def apply_theme(self):
        #Применяет текущую тему к окну
        if hasattr(self, 'setStyleSheet'):
            self.setStyleSheet(self.settings.get_theme_stylesheet())
    
    def update_language(self):
        #Обновляет текст на всех элементах 
        pass
    
    def on_settings_changed(self):
        #Обработчик изменения глобальных настроек
        self.apply_theme()
        self.update_language()
        