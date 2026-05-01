from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Signal
from pathlib import Path
import sys

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path / "interface" / "Go_app" / "generated"))

from generated.ui_game_settings_dialog_pve import Ui_GameSettingsDialogPVE


class GameSettingsDialogPVE(QDialog):
    settings_applied = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GameSettingsDialogPVE()
        self.ui.setupUi(self)
        
        # Подключаем кнопки
        self.ui.buttonOk.clicked.connect(self.on_ok)
        self.ui.buttonCancel.clicked.connect(self.reject)
        
    def get_board_size(self):
        if self.ui.radio9x9.isChecked():
            return 9
        elif self.ui.radio13x13.isChecked():
            return 13
        else:
            return 19
            
    def get_player_color(self):
        return self.ui.radioBlack.isChecked()
    
    def get_visual_settings(self):
        return {
            'show_legal_moves': self.ui.checkLegalMoves.isChecked()
        }
        
    def on_ok(self):
        settings = {
            'board_size': self.get_board_size(),
            'player_is_black': self.get_player_color(),
            'visual': self.get_visual_settings(),
            'time': {'no_time_limit': True}
        }
        self.settings_applied.emit(settings)
        self.accept()