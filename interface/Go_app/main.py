import sys
from PySide6.QtWidgets import QApplication, QWidget
from windows.game_windowPvP import GameWindow
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent
print(f"Project root: {root_path}")
sys.path.append(str(root_path / "scripts"))
sys.path.append(str(root_path / "interface" / "Go_app"))

import go_engine as go
from generated.ui_form import Ui_mainWindow
from windows.game_setting_dialog import GameSettingsDialog  # Исправлено имя файла

class MainTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        
        # Подключаем кнопку
        self.ui.buttonWindOffline.clicked.connect(self.open_offline_game)
        
        self.game_window = None
    
    def open_offline_game(self):
        """Открыть диалог настроек перед игрой"""
        dialog = GameSettingsDialog(self)
        
        def start_game(settings):
            self.hide()
            
            # Создаем core_api с размером из настроек
            core_api = go.Game(settings['board_size'])
            
            # НЕ передаем board_size отдельно, только core_api и settings
            self.game_window = GameWindow(
                navigation=None,
                core_api=core_api,
                settings=settings  # board_size уже внутри settings
            )
            
            self.game_window.game_finished.connect(self.on_game_finished)
            self.game_window.show()
        
        dialog.settings_applied.connect(start_game)
        dialog.exec()

    def on_game_finished(self):
        """Когда игра закончена: скрываем GameWindow и показываем главное"""
        if self.game_window:
            self.game_window.hide()
            self.game_window = None
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainTestWindow()
    window.show()
    sys.exit(app.exec())