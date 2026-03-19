import sys
from PySide6.QtWidgets import QApplication
from windows.game_window import GameWindow
from core.fake_core_for_test import MockCoreAPI   #REAL_IMPORT

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    #REAL_CORE_INSTANTIATE_HERE
    core_api = MockCoreAPI(19)
    
    window = GameWindow(navigation=None, board_size=19, core_api=core_api)
    window.show()
    sys.exit(app.exec())