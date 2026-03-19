from PySide6.QtWidgets import QWidget

class BaseWindow(QWidget):
    """
    Базовый класс для всех окон приложения.
    Содержит общую логику и доступ к навигации.
    """
    
    def __init__(self, navigation, parent=None):
        super().__init__(parent)
        self.navigation = navigation
        