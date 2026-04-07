import sys
import os
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QProgressDialog
from PySide6.QtCore import Qt,  QThread, Signal


#НЕ ТАК
# from generated.ui_game_window import Ui_main 
# from windows.base_window import BaseWindow
# from windows.profile_window import ProfileWindow
# import go_engine  as go
# from GnuGo_Analyzer import get_winner


import sys
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent.parent
# print(f"Project root: {root_path}")

sys.path.append(str(root_path / "scripts"))
import go_engine as go

sys.path.append(str(root_path / "interface" / "Go_app" ))
from windows.base_window import BaseWindow
from windows.profile_window import ProfileWindow
from generated.ui_game_window import Ui_main 
import GnuGo_Analyzer as gnugo
root_path = Path(__file__).resolve().parent.parent.parent.parent
GNUGO_PATH = os.path.join(root_path, "bot", "gnugo-3.8", "gnugo.exe")
print(f"GNUGO_PATH: {GNUGO_PATH}")
print(f"Существует: {os.path.exists(GNUGO_PATH)}")


class GameWindow(BaseWindow):
    game_finished = Signal()

    class GnuGoAnalysisTask(QThread):
        finished = Signal(object)  # результат анализа
        error = Signal(object)     # исключение

        def __init__(self, sgf, board_size, gnugo_path):
            super().__init__()
            self.sgf = sgf
            self.board_size = board_size
            self.gnugo_path = gnugo_path

        def run(self):
            try:
                analyzer = gnugo.GnuGoAnalyzer(gnugo_path=self.gnugo_path)
                try:
                    result = analyzer.analyze_sgf(self.sgf, self.board_size)
                finally:
                    analyzer.cleanup()
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(e)

    def __init__(self, navigation, board_size=9, core_api=None):
        super().__init__(navigation)
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.board_size = board_size
        self.core_api = core_api
        self.board_widget = self.ui.boardWidget
        self.board_widget.set_board_size(board_size)
        if self.core_api:
            self.board_widget.set_core_api(self.core_api)
        
        self.board_widget.cell_clicked.connect(self.on_cell_clicked)
        self.board_widget.move_made.connect(self.on_move_made)
        #self.board_widget.game_over.connect(self.on_game_over)
        #self.board_widget.invalid_move.connect(self.on_invalid_move)

        self.player_data = {
            'name': 'Игрок', 'rating': 1600, 'wins': 42, 'losses': 17,
            'country': 'Россия', 'avatar_path': None
        }
        self.opponent_data = {
            'name': 'Противник', 'rating': 1850, 'wins': 127, 'losses': 83,
            'country': 'США', 'avatar_path': None
        }
        self.ui.playerName.setText(self.player_data['name'])
        self.ui.opponentName.setText(self.opponent_data['name'])
        self.ui.playerAvatar.clicked.connect(self.show_player_profile)
        self.ui.opponentAvatar.clicked.connect(self.show_opponent_profile)
        self.ui.buttonPass.clicked.connect(self.pass_move)
        self.ui.buttonResign.clicked.connect(self.resign)
        self.ui.timerOpponent.setText("15:00")
        self.ui.timerPlayer.setText("15:00")
        self.ui.buttonPrevMove.clicked.connect(self.prev_move)
        self.ui.buttonNextMove.clicked.connect(self.next_move)
        self.move_history = []
        
        self.consecutive_passes = 0  #Счетчик последовательных пасов
        self.game_ended = False  #Флаг окончания игры
        self.winner = None  #Победитель (1 - черные, 2 - белые)

        self.setWindowTitle(f"Игра Го {board_size}×{board_size}")

    def show_player_profile(self):
        profile = ProfileWindow(self.player_data, self)
        profile.exec_()

    def show_opponent_profile(self):
        profile = ProfileWindow(self.opponent_data, self)
        profile.exec_()

    def on_cell_clicked(self, row, col):
        if not self.game_ended: 
            self.board_widget.request_move(row, col)


    def on_move_made(self, row, col, player):
        if self.game_ended:
            return
            
        player_name = "Черные" if player == 1 else "Белые"
        print(f"Ход {player_name}: ({row}, {col})")
        
        #Сбрасываем счетчик пасов при обычном ходе
        self.consecutive_passes = 0
        
        move_number = self.ui.historyList.count() + 1
        col_letter = chr(65 + col)
        move_text = f"{move_number}. {col_letter}{row + 1}"
        self.ui.historyList.addItem(move_text)
        
        #Прокручиваем историю к последнему ходу
        self.ui.historyList.scrollToBottom()

    def end_game_by_passes(self):
            if self.game_ended:
                return

            self.game_ended = True

            if not os.path.exists(GNUGO_PATH):
                QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
                self.game_finished.emit()
                return

            if not gnugo.check_gnugo_available(GNUGO_PATH):
                QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
                self.game_finished.emit()
                return

            if not self.core_api:
                QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
                self.game_finished.emit()
                return

            sgf = self.core_api.get_sgf()
            if not sgf or len(sgf) < 30:
                QMessageBox.information(
                    self, "Игра окончена",
                    "Игра завершена двумя пасами.\nАнализ недоступен: слишком короткая партия."
                )
                self.game_finished.emit()
                return

            dialog = QProgressDialog("Анализируем позицию с помощью GNU Go...", "Отмена", 0, 0, self)
            dialog.setWindowModality(Qt.WindowModal)
            dialog.show()

            self.analysis_task = self.GnuGoAnalysisTask(sgf, self.board_size, GNUGO_PATH)
            self.analysis_task.finished.connect(lambda result: self._on_analysis_finished(result, dialog))
            self.analysis_task.error.connect(lambda e: self._on_analysis_error(e, dialog))
            self.analysis_task.start()


    def _on_analysis_finished(self, result, dialog):
        dialog.close()

        if result and isinstance(result, dict):
            winner_text = result.get('winner', 'Не определен')
            QMessageBox.information(self, "Игра окончена", f"Победитель: {winner_text}!")
        else:
            QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")

        self.game_finished.emit()


    def _on_analysis_error(self, exception, dialog):
        dialog.close()
        QMessageBox.warning(
            self, "Ошибка анализа",
            f"Ошибка при анализе партии:\n{exception}\nИгра завершена без анализа."
        )
        self.game_finished.emit()

    def pass_move(self):
        print(f"=== pass_move, game_ended={self.game_ended}, consecutive_passes={self.consecutive_passes} ===")
        
        if self.game_ended:
            print("Игра окончена, пас игнорируется")
            return
            
        if self.board_widget.pass_move():
            self.consecutive_passes += 1
            move_number = self.ui.historyList.count() + 1
            self.ui.historyList.addItem(f"{move_number}. pass")
            self.ui.historyList.scrollToBottom()
            print(f"Пас выполнен ({self.consecutive_passes}/2)")
            
            if self.consecutive_passes >= 2:
                print("Достигнуто 2 паса, вызываем end_game_by_passes()")
                self.end_game_by_passes()
        else:
            print("Пас не удался") 
             

    #def on_invalid_move(self, row, col):
    #    print(f" Недопустимый ход в ({row}, {col})")


    def resign(self):
        reply = QMessageBox.question(self, "Сдаться",
                                   "Вы уверены, что хотите сдаться?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.game_ended = True 
            QMessageBox.information(self, "Игра окончена", "Вы сдались. Победил противник!")
            self.game_finished.emit()



    '''def on_game_over(self, _):
        if self.game_ended:
            return
            
        self.game_ended = True 
        
        if self.core_api:
            try:
                sgf = self.core_api.get_sgf()
                print(f" SGF получен: {len(sgf)} символов")
                
                gnu_winner = get_winner(sgf, self.board_size)
                
                winner_text = {
                    1: "Черные", 
                    2: "Белые", 
                    0: "Ничья", 
                    -1: "Не удалось определить"
                }.get(gnu_winner, "Неизвестно")
                
                if gnu_winner != -1:
                    QMessageBox.information(self, "Игра окончена", f"Победил: {winner_text}!")
                else:
                    QMessageBox.warning(self, "Ошибка анализа", 
                                      "Не удалось определить победителя.\nПроверьте работу GNU Go.")
            except Exception as e:
                print(f" Ошибка анализа SGF: {e}")
                QMessageBox.warning(self, "Ошибка", f"Ошибка анализа партии: {e}")
        self.game_finished.emit()

             
    '''    

    def prev_move(self):
        current = self.ui.historyList.currentRow()
        if current > 0:
            self.ui.historyList.setCurrentRow(current - 1)

    def next_move(self):
        current = self.ui.historyList.currentRow()
        if current < self.ui.historyList.count() - 1:
            self.ui.historyList.setCurrentRow(current + 1)
