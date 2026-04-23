# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QMessageBox
from navigation import Navigation
from windows.game_windowPvP import GameWindow
from generated.ui_form import Ui_mainWindow
from windows.game_setting_dialog import GameSettingsDialog

class Widget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
    
        self.navigation = Navigation(self.stacked_widget)
        
        self.main_menu = QWidget()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self.main_menu)
        
        self.navigation.add_window("main_menu", self.main_menu)

        self.ui.buttonWindOffline.clicked.connect(self.open_windOffline)
        self.ui.buttonWindOnline.clicked.connect(self.open_windOnline)
        self.ui.buttonWindBot.clicked.connect(self.open_windBot)
        self.ui.buttonInstruct.clicked.connect(self.open_windInstruct)

        self.ui.buttonAccount.clicked.connect(self.open_windAccount)
        self.ui.buttonSettings.clicked.connect(self.open_windSettings)
        self.navigation.navigate_to("main_menu")

    def open_windOffline(self):
        import go_engine as go
        core_api = go.Game(19)
        game_window = GameWindow(
            navigation=self.navigation,
            board_size=19,  
            core_api=None   
        )
        self.navigation.add_window("offline_game", game_window)
        
        # Подключаем сигнал закрытия для возврата в меню
        game_window.game_finished.connect(lambda: self.return_to_menu("offline_game"))
        
        # Переключаемся на игровое окно
        self.navigation.navigate_to("offline_game")


    def open_windOnline(self):
        print("Online button on the main window")
        QMessageBox.information(self,"Button", "open online window")

    def open_windBot(self):
        print("Bot button on the main window")
        QMessageBox.information(self,"Button", "open bot window")

    def open_windInstruct(self):
        print("Instruction button on the main window")
        QMessageBox.information(self,"Button", "open instruction window")

    def open_windAccount(self):
        print("Account button on the sidebar")
        QMessageBox.information(self,"Button", "open account window")

    def open_windSettings(self):
        print("Settings button on the sidebar")
        QMessageBox.information(self,"Button", "open settings window")

    def return_to_menu(self, window_name):
        # Удаляем окно из навигации
        if window_name in self.navigation.windows:
            # Получаем виджет и удаляем его
            widget = self.navigation.windows[window_name]
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()  # Безопасное удаление
            del self.navigation.windows[window_name]
        
        # Возвращаемся в главное меню
        self.navigation.navigate_to("main_menu")

    def open_windOffline(self):
        dialog = GameSettingsDialog(self)
        
        def start_game(settings):
            import go_engine as go
            
            core_api = go.Game(settings['board_size'])
            
            game_window = GameWindow(
                navigation=self.navigation,
                board_size=settings['board_size'],
                core_api=core_api,
                settings=settings
            )
            
            self.navigation.add_window("offline_game", game_window)
            game_window.game_finished.connect(lambda: self.return_to_menu("offline_game"))
            self.navigation.navigate_to("offline_game")
        
        dialog.settings_applied.connect(start_game)
        dialog.exec()    





if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
