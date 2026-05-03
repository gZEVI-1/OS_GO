import sys
import os
from copy import deepcopy
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QProgressDialog
from PySide6.QtCore import Qt,  QThread, Signal
from game_timer import GameTimer


#НЕ ТАК
# from generated.ui_game_window import Ui_main 
# from windows.base_window import BaseWindow
# from windows.profile_window import ProfileWindow
# import go_engine  as go
# from GnuGo_Analyzer import get_winner

from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent.parent
# print(f"Project root: {root_path}")

sys.path.append(str(root_path / "scripts"))
import go_engine as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(str(root_path / "interface" / "Go_app" ))
from windows.base_window import BaseWindow
from windows.profile_window import ProfileWindow
from generated.ui_game_windowPvP import Ui_main 
from windows.game_setting_dialog import GameSettingsDialog
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

    def __init__(self, navigation, core_api=None, settings=None):
        super().__init__(navigation)
        
        self.game_settings = settings or {
            'board_size': 9,
            'time': {'main_time': 900, 'byoyomi': 30},
            'visual': {'show_legal_moves': True}
        }
        
        #БЕРЕМ РАЗМЕР ИЗ НАСТРОЕК
        self.board_size = self.game_settings['board_size']
        
        #БАЗОВЫЕ ПАРАМЕТРЫ
        self.consecutive_passes = 0
        self.game_ended = False
        self.winner = None
        self.is_navigating = False
        
        #ИНИЦИАЛИЗАЦИЯ UI
        self.ui = Ui_main()
        self.ui.setupUi(self)
        
        #НАСТРОЙКА CORE API
        if core_api is None:
            import go_engine as go
            self.core_api = go.Game(self.board_size)
        else:
            self.core_api = core_api
        
        #НАСТРОЙКА ВИДЖЕТА ДОСКИ
        self.board_widget = self.ui.boardWidget 
        self.board_widget.set_core_api(self.core_api)       
        self.board_widget.set_board_size(self.board_size)

        show_legal = self.game_settings.get('visual', {}).get('show_legal_moves', True)
        self.board_widget.show_legal_moves = show_legal
        self.board_widget.update_legal_moves() 
        
        #ПОДКЛЮЧЕНИЕ СИГНАЛОВ
        self.board_widget.cell_clicked.connect(self.on_cell_clicked)
        self.board_widget.move_made.connect(self.on_move_made)
        
        #НАСТРОЙКА ТАЙМЕРОВ
        self.setup_timers()
        
        #НАСТРОЙКА НАВИГАЦИИ ПО ХОДАМ
        self.board_snapshots = []
        self.current_snapshot_index = -1
        self.move_descriptions = []
        
        #ДАННЫЕ ИГРОКОВ
        self.player_data = {
            'name': 'Игрок1', 'rating': 1600, 'wins': 42, 'losses': 17,
            'country': 'Россия', 'avatar_path': None
        }
        self.opponent_data = {
            'name': 'Игрок2', 'rating': 1850, 'wins': 127, 'losses': 83,
            'country': 'США', 'avatar_path': None
        }
        
        #НАСТРОЙКА UI ЭЛЕМЕНТОВ
        self.ui.playerName.setText(self.player_data['name'])
        self.ui.opponentName.setText(self.opponent_data['name'])
        self.ui.playerAvatar.clicked.connect(self.show_player_profile)
        self.ui.opponentAvatar.clicked.connect(self.show_opponent_profile)
        self.ui.buttonPass.clicked.connect(self.pass_move)
        self.ui.buttonResign.clicked.connect(self.resign)
        self.ui.buttonPrevMove.clicked.connect(self.prev_move)
        self.ui.buttonNextMove.clicked.connect(self.next_move)
        
        #ФИНАЛЬНЫЕ НАСТРОЙКИ
        self.setWindowTitle(f"Игра Го {self.board_size}×{self.board_size}")
        self.save_initial_snapshot()


    def update_language(self):
        # Обновляем заголовок окна
        self.setWindowTitle(f"{self.settings.get_text('game_title')} {self.board_size}×{self.board_size}")
        
        # Обновляем текст на кнопках
        self.ui.buttonPass.setText(self.settings.get_text("pass_button"))
        self.ui.buttonResign.setText(self.settings.get_text("resign_button"))
        
    def setup_timers(self):
            time_settings = self.game_settings.get('time', {})
            no_time_limit = time_settings.get('no_time_limit', False)
            
            self.initial_player_time = time_settings.get('main_time', 900) if not no_time_limit else 0
            self.initial_opponent_time = time_settings.get('main_time', 900) if not no_time_limit else 0
            self.byoyomi = time_settings.get('byoyomi', 30) if not no_time_limit else 0
            
            if no_time_limit:
                self.player_timer = GameTimer(1, 0, self, no_time_limit=True)
                self.opponent_timer = GameTimer(2, 0, self, no_time_limit=True)
                
                self.ui.timerPlayer.setText("--:--")
                self.ui.timerOpponent.setText("--:--")
                self.ui.timerPlayer.setStyleSheet("color: gray;")
                self.ui.timerOpponent.setStyleSheet("color: gray;")
            else:
                self.player_timer = GameTimer(1, self.initial_player_time, self, no_time_limit=False)
                self.opponent_timer = GameTimer(2, self.initial_opponent_time, self, no_time_limit=False)
                
                self.ui.timerPlayer.setStyleSheet("")
                self.ui.timerOpponent.setStyleSheet("")
                
                self.player_timer.time_changed.connect(self.update_timer_display)
                self.opponent_timer.time_changed.connect(self.update_timer_display)
                self.player_timer.time_expired.connect(self.on_time_expired)
                self.opponent_timer.time_expired.connect(self.on_time_expired)
                
                self.player_timer.start()
            
            self.update_timer_display()
    
    def update_timer_active(self):
        if self.game_ended:
            self.player_timer.stop()
            self.opponent_timer.stop()
            return
            
        if self.player_timer.no_time_limit:
            return
            
        if self.board_widget.current_player == 1:
            if not self.player_timer.is_running:
                self.opponent_timer.stop()
                self.player_timer.start()
        else:
            if not self.opponent_timer.is_running:
                self.player_timer.stop()
                self.opponent_timer.start()

    def update_timer_display(self):
        if self.player_timer.no_time_limit:
            return
        
        player_seconds = int(self.player_timer.time_remaining) 
        opponent_seconds = int(self.opponent_timer.time_remaining)
        
        player_min = player_seconds // 60
        player_sec = player_seconds % 60
        self.ui.timerPlayer.setText(f"{player_min:02d}:{player_sec:02d}")
        
        opponent_min = opponent_seconds // 60
        opponent_sec = opponent_seconds % 60
        self.ui.timerOpponent.setText(f"{opponent_min:02d}:{opponent_sec:02d}")

    def on_time_expired(self, player):
        if self.game_ended:
            return
            
        if self.player_timer.no_time_limit:
            return
            
        self.game_ended = True
        
        if player == 1:
            winner = "Белые"
            self.winner = 2
        else:
            winner = "Черные"
            self.winner = 1
        
        self.player_timer.stop()
        self.opponent_timer.stop()
        
        QMessageBox.information(self, "Время вышло", f"Время {winner} вышло! {winner} победили!")
        self.game_finished.emit()

    def save_initial_snapshot(self):
        snapshot = self.create_snapshot()
        self.board_snapshots.append(snapshot)
        self.current_snapshot_index = 0
        
        self.move_descriptions.append("Начало партии")
        
        self.update_navigation_buttons()

    def create_snapshot(self):
        return {
               
            'board_state': deepcopy(self.board_widget.board_state),
            'current_player': self.board_widget.current_player,
            'last_move': self.board_widget.last_move
        }
    
    def restore_snapshot(self, index):
        if not (0 <= index < len(self.board_snapshots)):
            return False
        snapshot = self.board_snapshots[index]

        self.board_widget.board_state = deepcopy(snapshot['board_state'])
        self.board_widget.current_player = snapshot['current_player']
        self.board_widget.last_move = snapshot['last_move']
        

        self.board_widget.update()
        
        self.update_history_selection(index)
        
        return True
    
    def save_initial_snapshot(self):
        snapshot = self.create_snapshot()
        self.board_snapshots.append(snapshot)
        self.current_snapshot_index = 0
        self.move_descriptions.append("Начало партии")
        self.update_navigation_buttons()

    def save_snapshot_after_move(self, move_description):
        if self.is_navigating:
            return
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
                self.board_snapshots = self.board_snapshots[:self.current_snapshot_index + 1]
                self.move_descriptions = self.move_descriptions[:self.current_snapshot_index + 1]

                self.ui.historyList.clear()
                for desc in self.move_descriptions:
                    self.ui.historyList.addItem(desc)
            
        snapshot = self.create_snapshot()
        self.board_snapshots.append(snapshot)
        self.move_descriptions.append(move_description)
        self.current_snapshot_index = len(self.board_snapshots) - 1
        
        self.update_navigation_buttons()

    def update_history_selection(self, snapshot_index):
        if snapshot_index > 0:
            history_index = snapshot_index - 1
            if 0 <= history_index < self.ui.historyList.count():
                self.ui.historyList.setCurrentRow(history_index)
        else:
            self.ui.historyList.clearSelection()

    def update_navigation_buttons(self):
        self.ui.buttonPrevMove.setEnabled(self.current_snapshot_index > 0)
        self.ui.buttonNextMove.setEnabled(self.current_snapshot_index < len(self.board_snapshots) - 1)

    def jump_to_latest(self):
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.is_navigating = True
            self.current_snapshot_index = len(self.board_snapshots) - 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_navigation_buttons()
            print(f"Возврат к актуальному состоянию")


    def prev_move(self):
        #Переход на один ход назад (только просмотр)
        if self.current_snapshot_index > 0:
            self.is_navigating = True
            self.current_snapshot_index -= 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_navigation_buttons()
            print(f"Навигация назад: ход {self.current_snapshot_index}/{len(self.board_snapshots)-1}")

    def next_move(self):
        #Переход на один ход вперед (только просмотр)
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self.is_navigating = True
            self.current_snapshot_index += 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_navigation_buttons()
            print(f"Навигация вперед: ход {self.current_snapshot_index}/{len(self.board_snapshots)-1}")  





    def show_player_profile(self):
        profile = ProfileWindow(self.player_data, self)
        profile.exec_()

    def show_opponent_profile(self):
        profile = ProfileWindow(self.opponent_data, self)
        profile.exec_()


    def on_cell_clicked(self, row, col):
        if self.game_ended:
            return
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.jump_to_latest()
        self.board_widget.request_move(row, col)

    def on_move_made(self, row, col, player):
        if self.game_ended:
            return

        move_number = (len(self.move_descriptions) - 1) // 2 + 1
        
        col_letter = chr(65 + col)
        player_name = "Черные" if player == 1 else "Белые"
        move_desc = f"{move_number}. {player_name}: {col_letter}{row + 1}"
        self.ui.historyList.addItem(move_desc)
        self.ui.historyList.scrollToBottom()

        self.save_snapshot_after_move(move_desc)

        self.update_timer_active()
        # Сбрасываем счетчик пасов при обычном ходе
        self.consecutive_passes = 0


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
            self.analysis_task.finished.connect(lambda result: self.on_analysis_finished(result, dialog))
            self.analysis_task.error.connect(lambda e: self.on_analysis_error(e, dialog))
            self.analysis_task.start()


    def on_analysis_finished(self, result, dialog):
        dialog.close()

        if result and isinstance(result, dict):
            winner_text = result.get('winner', 'Не определен')
            QMessageBox.information(self, "Игра окончена", f"Победитель: {winner_text}!")
        else:
            QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")

        self.game_finished.emit()


    def on_analysis_error(self, exception, dialog):
        dialog.close()
        QMessageBox.warning(
            self, "Ошибка анализа",
            f"Ошибка при анализе партии:\n{exception}\nИгра завершена без анализа."
        )
        self.game_finished.emit()

    def pass_move(self):
        
        if self.game_ended:
            print("Игра окончена, пас игнорируется")
            return
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.jump_to_latest()
            
        if self.board_widget.pass_move():
            self.consecutive_passes += 1
            
            move_number = (len(self.move_descriptions) - 1) // 2 + 1
            move_desc = f"{move_number}. Пас"
            self.ui.historyList.addItem(move_desc)
            self.ui.historyList.scrollToBottom()
            self.save_snapshot_after_move(move_desc)

            self.update_timer_active()

            if self.consecutive_passes >= 2:
                self.end_game_by_passes()
        else:
            print("Пас не удался")
             

    #def on_invalid_move(self, row, col):
    #    print(f" Недопустимый ход в ({row}, {col})")


    def resign(self):
        reply = QMessageBox.question(self, 
                                self.settings.get_text("resign_title"),
                                self.settings.get_text("resign_confirm"),
                                QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.game_ended = True 
            QMessageBox.information(self, self.settings.get_text("game_ended"), 
                                self.settings.get_text("opponent_won"))
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
