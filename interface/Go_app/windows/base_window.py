from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject
from windows.app_settings import AppSettings

class BaseWindow(QWidget):
    
    def __init__(self, navigation, parent=None):
        super().__init__(parent)
        self.navigation = navigation
        self.settings = AppSettings()  
        
        self.settings.settings_changed.connect(self.on_settings_changed)
        
        self.apply_theme()
    
    def apply_theme(self):
        if hasattr(self, 'setStyleSheet'):
            self.setStyleSheet(self.settings.get_stylesheet())
    
    def update_language(self):
        pass
    
    def on_settings_changed(self):
        self.apply_theme()
        self.update_language()