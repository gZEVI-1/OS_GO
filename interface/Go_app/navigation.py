from PySide6.QtWidgets import QStackedWidget, QWidget
from PySide6.QtCore import QObject, Signal

class Navigation(QObject):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.windows = {}
    
    def add_window(self, name, window):
        #Добавить окно в навигацию
        self.windows[name] = window
        self.stacked_widget.addWidget(window)
    
    def navigate_to(self, name):
        #Переключиться на указанное окно
        if name in self.windows:
            self.stacked_widget.setCurrentWidget(self.windows[name])
            print(f"Navigated to: {name}")
    
    def get_window(self, name):
        #Получить окно по имени
        return self.windows.get(name)
