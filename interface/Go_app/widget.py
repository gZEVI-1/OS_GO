# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import QSize
from navigation import Navigation
from windows.game_windowPvP import GameWindow
from windows.game_windowPvE import GameWindowPvE
from generated.ui_form import Ui_mainWindow
from windows.game_setting_dialog import GameSettingsDialog
from windows.game_settings_dialog_pve import GameSettingsDialogPVE
from PySide6.QtWidgets import QSizePolicy


class Widget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Устанавливаем размер окна как в UI
        self.setMinimumSize(1109, 781)
        self.resize(1109, 781)
        
        # Центрируем окно на экране
        self.center_window()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
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
    
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def open_windOffline(self):
        dialog = GameSettingsDialog(self)
        
        def start_game(settings):
            import go_engine as go
            
            core_api = go.Game(settings['board_size'])
            
            game_window = GameWindow(
                navigation=self.navigation,
                core_api=core_api,
                settings=settings
            )

            game_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            self.navigation.add_window("offline_game", game_window)
            game_window.game_finished.connect(lambda: self.return_to_menu("offline_game"))
            self.navigation.navigate_to("offline_game")
        
        dialog.settings_applied.connect(start_game)
        dialog.exec()

    def open_windBot(self):
        dialog = GameSettingsDialogPVE(self)
        
        def start_game(settings):
            import go_engine as go
            
            core_api = go.Game(settings['board_size'])
            
            game_window = GameWindowPvE(
                navigation=self.navigation,
                core_api=core_api,
                settings=settings
            )
            
            # Настройка растяжения для всего контента
            game_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            self.navigation.add_window("bot_game", game_window)
            game_window.game_finished.connect(lambda: self.return_to_menu("bot_game"))
            self.navigation.navigate_to("bot_game")
        
        dialog.settings_applied.connect(start_game)
        dialog.exec()

    def open_windOnline(self):
        print("Online button on the main window")
        QMessageBox.information(self, "Button", "open online window")

    def open_windInstruct(self):
        print("Instruction button on the main window")
        QMessageBox.information(self, "Button", "open instruction window")

    def open_windAccount(self):
        print("Account button on the sidebar")
        QMessageBox.information(self, "Button", "open account window")

    def open_windSettings(self):
        print("Settings button on the sidebar")
        QMessageBox.information(self, "Button", "open settings window")

    def return_to_menu(self, window_name):
        if window_name in self.navigation.windows:
            widget = self.navigation.windows[window_name]
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
            del self.navigation.windows[window_name]
        
        self.navigation.navigate_to("main_menu")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())