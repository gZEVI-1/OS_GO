import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from navigation import Navigation
from windows.game_windowPvP import GameWindow
from windows.game_windowPvE import GameWindowPvE
from generated.ui_form import Ui_mainWindow
from windows.game_setting_dialog import GameSettingsDialog
from windows.game_settings_dialog_pve import GameSettingsDialogPVE
from PySide6.QtWidgets import QSizePolicy
from windows.app_settings import AppSettings
from windows.settings_dialog import SettingsDialog
from windows.online_lobby import OnlineLobbyDialog
from windows.game_windowOnline import GameWindowOnline


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
        
        self.settings = AppSettings()
        self.main_menu = QWidget()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self.main_menu)
        
        # ========== НАСТРОЙКА ИКОНОК ==========
        self.setup_icon_buttons()
        
        self.navigation.add_window("main_menu", self.main_menu)

        self.ui.buttonWindOffline.clicked.connect(self.open_windOffline)
        self.ui.buttonWindOnline.clicked.connect(self.open_windOnline)
        self.ui.buttonWindBot.clicked.connect(self.open_windBot)
        self.ui.buttonInstruct.clicked.connect(self.open_windInstruct)

        self.ui.buttonAccount.clicked.connect(self.open_windAccount)
        self.ui.buttonSettings.clicked.connect(self.open_windSettings)
        
        self.navigation.navigate_to("main_menu")
        self.update_main_menu_language()
        self.apply_theme()
        self.settings.settings_changed.connect(self.on_settings_changed)

    def setup_icon_buttons(self):
        icon_buttons = {
            self.ui.buttonWindBot: "bot",
            self.ui.buttonWindOffline: "offline",
            self.ui.buttonWindOnline: "online",
            self.ui.buttonSettings: "settings"
        }
        
        for button, icon_name in icon_buttons.items():
            button._icon_name = icon_name
            self.update_button_icon(button)
    
    def update_button_icon(self, button):
        if not hasattr(button, '_icon_name'):
            return
        
        icon_name = button._icon_name
        icon_path = self.settings.get_icon_path(icon_name)
        
        if icon_path:
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(32, 32))
            
            if icon_name == "settings":
                button.setText("")
    
    def update_all_icons(self):
        buttons = [
            self.ui.buttonWindBot,
            self.ui.buttonWindOffline,
            self.ui.buttonWindOnline,
            self.ui.buttonSettings
        ]
        
        for button in buttons:
            self.update_button_icon(button)
    
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
            
            game_window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            self.navigation.add_window("bot_game", game_window)
            game_window.game_finished.connect(lambda: self.return_to_menu("bot_game"))
            self.navigation.navigate_to("bot_game")
        
        dialog.settings_applied.connect(start_game)
        dialog.exec()

    def open_windOnline(self):
       #player_name = self.settings.get("player_name", "Player")
        player_name = "Player"
        dialog = OnlineLobbyDialog(player_name, self)
        dialog.game_ready.connect(self.start_online_game)
        dialog.exec()
    
    def start_online_game(self, game_data):
        game_window = GameWindowOnline(
            navigation=self.navigation,
            client=game_data["client"],
            player_name=game_data["player_name"],
            player_color=game_data["player_color"],
            board_size=game_data["board_size"],
            time_settings=game_data["time_settings"],
            visual_settings=game_data["visual_settings"]
        )
        self.navigation.add_window("online_game", game_window)
        game_window.game_finished.connect(lambda: self.return_to_menu("online_game"))
        self.navigation.navigate_to("online_game")

    def open_windInstruct(self):
        from windows.rules_window import RulesWindow
        rules_window = RulesWindow(self.navigation, parent=self)
        self.navigation.add_window("rules", rules_window)
        self.navigation.navigate_to("rules")

    def open_windAccount(self):
        print("Account button on the sidebar")
        QMessageBox.information(self, "Button", "open account window")

    def open_windSettings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def return_to_menu(self, window_name):
        if window_name in self.navigation.windows:
            widget = self.navigation.windows[window_name]
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
            del self.navigation.windows[window_name]
        
        self.navigation.navigate_to("main_menu")

    def apply_theme(self):
        stylesheet = self.settings.get_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)
        
        for i in range(self.stacked_widget.count()):
            widget = self.stacked_widget.widget(i)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

    def update_main_menu_language(self):
        self.ui.buttonWindOnline.setText(self.settings.get_text("open_online"))
        self.ui.buttonWindOffline.setText(self.settings.get_text("open_offline"))
        self.ui.buttonWindBot.setText(self.settings.get_text("open_bot"))
        self.ui.buttonInstruct.setText(self.settings.get_text("open_instruction"))

    def on_settings_changed(self):
        self.apply_theme()
        self.update_main_menu_language()
        self.update_all_icons()  

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())