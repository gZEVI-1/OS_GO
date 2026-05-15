from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Signal
from pathlib import Path
import sys

root_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_path / "interface" / "Go_app" / "generated"))

from generated.ui_game_setting_dialog import Ui_GameSettingsDialog

class GameSettingsDialog(QDialog):
    settings_applied = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GameSettingsDialog()
        self.ui.setupUi(self)
        
        # Подключаем кнопки
        self.ui.buttonOk.clicked.connect(self.on_ok)
        self.ui.buttonCancel.clicked.connect(self.reject)
        
        # Настройка валидации
        self.ui.spinPlayerTime.setRange(1, 60)
        self.ui.spinByoyomi.setRange(0, 60)
        
        # Подключаем чекбокс "без лимита"
        self.ui.checkNoTimeLimit.toggled.connect(self.on_no_time_limit_toggled)
        
        # Изначальное состояние
        self.on_no_time_limit_toggled(self.ui.checkNoTimeLimit.isChecked())
        
    def on_no_time_limit_toggled(self, checked):
        self.ui.spinPlayerTime.setEnabled(not checked)
        self.ui.spinByoyomi.setEnabled(not checked)
        self.ui.labelPlayerTime.setEnabled(not checked)
        self.ui.labelByoyomi.setEnabled(not checked)
        
    def get_board_size(self):
        if self.ui.radio9x9.isChecked():
            return 9
        elif self.ui.radio13x13.isChecked():
            return 13
        else:
            return 19
            
    def get_time_settings(self):
        no_time_limit = self.ui.checkNoTimeLimit.isChecked()
        
        if no_time_limit:
            return {
                'no_time_limit': True,
                'main_time': None,
                'byoyomi': None
            }
        else:
            return {
                'no_time_limit': False,
                'main_time': self.ui.spinPlayerTime.value() * 60,  # в секундах
                'byoyomi': self.ui.spinByoyomi.value()
            }
        
    def get_visual_settings(self):
        return {
            'show_legal_moves': self.ui.checkLegalMoves.isChecked()
        }
        
    def on_ok(self):
        settings = {
            'board_size': self.get_board_size(),
            'time': self.get_time_settings(),
            'visual': self.get_visual_settings()
        }
        self.settings_applied.emit(settings)
        self.accept()