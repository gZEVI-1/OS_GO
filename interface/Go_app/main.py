import sys
from PySide6.QtWidgets import QApplication
from windows.game_window import GameWindow
import go_engine as go


if __name__ == "__main__":
    app = QApplication(sys.argv)
    core_api = go.Game(19)
    
    window = GameWindow(navigation=None, board_size=19, core_api=core_api)
    window.show()
    sys.exit(app.exec())
