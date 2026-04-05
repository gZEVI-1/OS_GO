import sys
from PySide6.QtWidgets import QApplication, QWidget
from windows.game_window import GameWindow
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent
print(f"Project root: {root_path}")
sys.path.append(str(root_path / "scripts"))
sys.path.append(str(root_path / "interface" / "Go_app"))
import go_engine as go
from windows.game_window import GameWindow
from generated.ui_form import Ui_mainWindow

class MainTestWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)
        
        # Подключаем кнопку
        self.ui.buttonWindOffline.clicked.connect(self.open_offline_game)
        
        self.game_window = None
    
    def open_offline_game(self):
        """Открыть офлайн игру"""
        # Скрываем главное окно
        self.hide()

        # Создаем игровое окно
        core_api = go.Game(9)
        self.game_window = GameWindow(
            navigation=None,
            board_size=9,
            core_api=core_api
        )

        # Подключаем сигнал завершения игры
        self.game_window.game_finished.connect(self.on_game_finished)

        self.game_window.show()


    def on_game_finished(self):
        """Когда игра закончена: скрываем GameWindow и показываем главное"""
        if self.game_window:
            self.game_window.hide()      # или .close(), но тогда с осторожностью
            self.game_window = None
        self.show()  # показываем главное меню
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainTestWindow()
    window.show()
    sys.exit(app.exec())
