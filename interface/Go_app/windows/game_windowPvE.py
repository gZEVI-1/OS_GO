import sys
import os
from copy import deepcopy
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal, QTimer

from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent.parent

sys.path.append(str(root_path / "scripts"))
import go_engine as go

sys.path.append(str(root_path / "interface" / "Go_app"))
from windows.base_window import BaseWindow
from windows.profile_window import ProfileWindow
from generated.ui_game_windowPvE import Ui_main
import GnuGo_Analyzer as gnugo

GNUGO_PATH = os.path.join(root_path, "bot", "gnugo-3.8", "gnugo.exe")

class BotMoveThread(QThread):
    """Поток для поиска хода бота"""
    move_ready = Signal(int, int)
    gnugo_error = Signal(str)  # Передаем текст ошибки
    
    def __init__(self, core_api, board_size, player_is_black):
        super().__init__()
        self.core_api = core_api
        self.board_size = board_size
        self.player_is_black = player_is_black
        
    def run(self):
        try:
            # Подавляем cygwin warning
            os.environ['CYGWIN'] = 'nodosfilewarning'
            
            if not os.path.exists(GNUGO_PATH):
                self.gnugo_error.emit(f"GNU Go не найден по пути: {GNUGO_PATH}")
                return
            
            if not gnugo.check_gnugo_available(GNUGO_PATH):
                self.gnugo_error.emit("GNU Go не отвечает")
                return
            
            sgf = self.core_api.get_sgf()
            if not sgf:
                self.gnugo_error.emit("Не удалось получить SGF")
                return
            
            current_player = self.core_api.get_current_player()
            is_black_turn = (current_player == go.Color.Black)
            move = self._get_gnugo_move(sgf, is_black_turn)
            
            if move:
                row, col = move
                if row >= 0 and col >= 0:
                    self.move_ready.emit(row, col)
                else:
                    self.move_ready.emit(-1, -1)
            else:
                self.gnugo_error.emit("GNU Go не вернул корректный ход")
                
        except Exception as e:
            print(f"Ошибка при ходе бота: {e}")
            self.gnugo_error.emit(str(e))
    
    def _get_gnugo_move(self, sgf, is_black_turn):
        try:
            import tempfile
            import re
            import subprocess
            
            temp_dir = tempfile.mkdtemp()
            
            try:
                sgf_file = os.path.join(temp_dir, "game.sgf")
                with open(sgf_file, 'w', encoding='utf-8') as f:
                    f.write(sgf)
                
                color = "black" if is_black_turn else "white"
                
                cmd = [
                    GNUGO_PATH,
                    "--mode", "gtp",
                    "--boardsize", str(self.board_size),
                    "--chinese-rules",
                    "--komi", "6.5"
                ]
                
                commands = f"loadsgf {sgf_file}\ngenmove {color}\nquit\n"
                
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(commands, timeout=10)
                
                # Парсим вывод
                for line in stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('='):
                        move_str = line[1:].strip()
                        
                        if move_str.upper() == "PASS":
                            return (-1, -1)
                        
                        # Проверяем, что строка похожа на координаты (буквы + цифры)
                        if re.match(r'^[A-Za-z]+[0-9]+$', move_str):
                            move_match = self._parse_gnugo_move(move_str)
                            if move_match:
                                row, col = move_match
                                if 0 <= row < self.board_size and 0 <= col < self.board_size:
                                    return (row, col)
                        else:
                            # Это не координаты (например, "White" или "Black")
                            print(f"GNU Go вернул не координаты: {move_str}")
                            continue
                
                return None
                
            finally:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except subprocess.TimeoutExpired:
            print("GNU Go timeout")
            return None
        except Exception as e:
            print(f"Ошибка GNU Go: {e}")
            return None
    
    def _parse_gnugo_move(self, move_str):
        """
        Парсит ход от GNU Go.
        Поддерживает форматы: "A1", "T10", "K19"
        """
        import re
        
        move_str = move_str.strip().upper()
        
        if not re.match(r'^[A-Z]+[0-9]+$', move_str):
            return None
        
        match = re.match(r'^([A-Z]+)([0-9]+)$', move_str)
        if not match:
            return None
        
        letters = match.group(1)
        
        try:
            row_num = int(match.group(2))
        except ValueError:
            return None
        
        # Преобразуем буквы в номер столбца
        col = 0
        for ch in letters:
            col = col * 26 + (ord(ch) - ord('A') + 1)
        col -= 1
        
        row = row_num - 1
        
        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            return None
        
        return (row, col)

class GameWindowPvE(BaseWindow):
    game_finished = Signal()

    class GnuGoAnalysisTask(QThread):
        finished = Signal(object)
        error = Signal(object)

        def __init__(self, sgf, board_size, gnugo_path):
            super().__init__()
            self.sgf = sgf
            self.board_size = board_size
            self.gnugo_path = gnugo_path

        def run(self):
            try:
                if not os.path.exists(self.gnugo_path):
                    self.error.emit("GNU Go не найден")
                    return
                
                if not gnugo.check_gnugo_available(self.gnugo_path):
                    self.error.emit("GNU Go не отвечает")
                    return
                
                winner = gnugo.get_winner(self.sgf, self.board_size)
                self.finished.emit(winner)
            except Exception as e:
                self.error.emit(e)

    def __init__(self, navigation, core_api=None, settings=None):
        super().__init__(navigation)
        
        # Загружаем настройки
        self.game_settings = settings or {
            'board_size': 9,
            'player_is_black': True,
            'visual': {'show_legal_moves': True},
            'time': {'no_time_limit': True}
        }
        
        self.board_size = self.game_settings['board_size']
        self.player_is_black = self.game_settings['player_is_black']
        
        # Базовые параметры
        self.consecutive_passes = 0
        self.game_ended = False
        self.winner = None
        self.is_navigating = False
        self.is_bot_thinking = False
        self.bot_move_timer = QTimer()
        self.bot_move_timer.setSingleShot(True)
        self.bot_move_timer.timeout.connect(self.make_bot_move)
        self.gnugo_error_occurred = False
        
        # Инициализация UI
        self.ui = Ui_main()
        self.ui.setupUi(self)
        
        # Настройка Core API
        if core_api is None:
            self.core_api = go.Game(self.board_size)
        else:
            self.core_api = core_api
        
        # Настройка виджета доски
        self.board_widget = self.ui.boardWidget
        self.board_widget.set_core_api(self.core_api)
        self.board_widget.set_board_size(self.board_size)
        
        # Визуальные настройки
        show_legal = self.game_settings.get('visual', {}).get('show_legal_moves', True)
        self.board_widget.show_legal_moves = show_legal
        self.board_widget.update_legal_moves()
        
        # Подключение сигналов
        self.board_widget.cell_clicked.connect(self.on_cell_clicked)
        self.board_widget.move_made.connect(self.on_move_made)
        
        # Настройка навигации по ходам
        self.board_snapshots = []
        self.current_snapshot_index = -1
        self.move_descriptions = []
        
        # Данные игрока
        self.player_data = {
            'name': 'Игрок', 'rating': 1600, 'wins': 42, 'losses': 17,
            'country': 'Россия', 'avatar_path': None
        }
        
        # Настройка отображения для PvE
        # Скрываем ненужные элементы
        self.ui.opponentAvatar.hide()
        self.ui.timerPlayer.hide()
        self.ui.timerOpponent.hide()
        
        # Вставляем метку вместо скрытого opponentName
        parent_layout = self.ui.opponentName.parent().layout()
        if parent_layout:
            index = parent_layout.indexOf(self.ui.opponentName)
            if index >= 0:
                parent_layout.insertWidget(index, self.bot_label)
        
        # Настройка имен с цветом
        if self.player_is_black:
            self.ui.playerName.setText(f"{self.player_data['name']} (Черные)")
            self.ui.opponentName.setText("GNU Go Bot (Белые)")
        else:
            self.ui.playerName.setText(f"{self.player_data['name']} (Белые)")
            self.ui.opponentName.setText("GNU Go Bot (Черные)")
        
        
        # Подключаем сигналы
        self.ui.playerAvatar.clicked.connect(self.show_player_profile)
        
        try:
            self.ui.opponentAvatar.clicked.disconnect()
        except:
            pass
        
        self.ui.buttonPass.clicked.connect(self.pass_move)
        self.ui.buttonResign.clicked.connect(self.resign)
        self.ui.buttonPrevMove.clicked.connect(self.prev_move)
        self.ui.buttonNextMove.clicked.connect(self.next_move)
        
        self.setWindowTitle(f"Игра с ботом GNU Go {self.board_size}×{self.board_size}")
        self.save_initial_snapshot()
        
        # Проверяем GNU Go перед стартом
        if not self.check_gnugo_available():
            return
        
        # Если игрок играет белыми (бот ходит первым)
        if not self.player_is_black and not self.game_ended:
            QTimer.singleShot(500, self.make_bot_move)
    
    def check_gnugo_available(self):
        """Проверяет доступность GNU Go"""
        if not os.path.exists(GNUGO_PATH):
            QMessageBox.critical(
                self, 
                "Ошибка GNU Go", 
                "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
            )
            self.game_ended = True
            self.game_finished.emit()
            return False
        
        if not gnugo.check_gnugo_available(GNUGO_PATH):
            QMessageBox.critical(
                self, 
                "Ошибка GNU Go", 
                "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
            )
            self.game_ended = True
            self.game_finished.emit()
            return False
        
        return True

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

    def prev_move(self):
        if self.current_snapshot_index > 0:
            self.is_navigating = True
            self.current_snapshot_index -= 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_navigation_buttons()

    def next_move(self):
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self.is_navigating = True
            self.current_snapshot_index += 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_navigation_buttons()

    def show_player_profile(self):
        profile = ProfileWindow(self.player_data, self)
        profile.exec_()

    def on_cell_clicked(self, row, col):
        if self.game_ended or self.is_bot_thinking or self.gnugo_error_occurred:
            return
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.jump_to_latest()
        
        current_player = self.board_widget.current_player
        is_player_turn = (current_player == 1 and self.player_is_black) or \
                        (current_player == 2 and not self.player_is_black)
        
        if is_player_turn:
            self.board_widget.request_move(row, col)

    def on_move_made(self, row, col, player):
        if self.game_ended or self.gnugo_error_occurred:
            return

        move_number = (len(self.move_descriptions) - 1) // 2 + 1
            
        col_letter = chr(65 + col)
        player_name = "Черные" if player == 1 else "Белые"
        
        is_player_move = (player == 1 and self.player_is_black) or \
                        (player == 2 and not self.player_is_black)
        who = "Игрок" if is_player_move else "Бот"
        
        move_desc = f"{move_number}. {who} ({player_name}): {col_letter}{row + 1}"
        self.ui.historyList.addItem(move_desc)
        self.ui.historyList.scrollToBottom()

        self.save_snapshot_after_move(move_desc)
        self.consecutive_passes = 0
        
        if not self.game_ended and is_player_move:
            self.bot_move_timer.start(300)

    def make_bot_move(self):
        """Ход бота через GNU Go"""
        if self.game_ended or self.is_bot_thinking or self.gnugo_error_occurred:
            return
            
        current_player = self.board_widget.current_player
        is_bot_turn = (current_player == 1 and not self.player_is_black) or \
                    (current_player == 2 and self.player_is_black)
        
        if not is_bot_turn:
            return
        
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.jump_to_latest()
        
        self.is_bot_thinking = True
        self.ui.buttonPass.setEnabled(False)
        self.ui.buttonResign.setEnabled(False)
        
        self.bot_thread = BotMoveThread(self.core_api, self.board_size, self.player_is_black)
        self.bot_thread.move_ready.connect(self.on_bot_move_ready)
        self.bot_thread.gnugo_error.connect(self.on_gnugo_error)
        self.bot_thread.start()
    
    def on_gnugo_error(self):
            self.is_bot_thinking = False
            self.ui.buttonPass.setEnabled(True)
            self.ui.buttonResign.setEnabled(True)
            
            if not self.game_ended:
                self.gnugo_error_occurred = True
                self.game_ended = True
                
                # Выводим конкретную причину ошибки, если есть
                #if error_message:
                #    print(f"Ошибка GNU Go: {error_message}")
                
                QMessageBox.critical(
                    self, 
                    "Ошибка GNU Go", 
                    "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
                )
                self.game_finished.emit()
    
    def on_bot_move_ready(self, row, col):
        self.is_bot_thinking = False
        self.ui.buttonPass.setEnabled(True)
        self.ui.buttonResign.setEnabled(True)
        
        if self.game_ended:
            return
            
        if row == -1 or col == -1:
            self.bot_pass_move()
        else:
            success = self.board_widget.request_move(row, col)
            if not success:
                self.bot_pass_move()
    
    def bot_pass_move(self):
        if self.board_widget.pass_move():
            self.consecutive_passes += 1
            
            # Номер хода не увеличиваем при пасе
            move_number = (len(self.move_descriptions) - 1) // 2 + 1
            move_desc = f"{move_number}. Пас (бот)"
            self.ui.historyList.addItem(move_desc)
            self.ui.historyList.scrollToBottom()
            self.save_snapshot_after_move(move_desc)

            if self.consecutive_passes >= 2:
                self.end_game_by_passes()

    def pass_move(self):
        if self.game_ended or self.is_bot_thinking or self.gnugo_error_occurred:
            return
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.jump_to_latest()
            
        current_player = self.board_widget.current_player
        is_player_turn = (current_player == 1 and self.player_is_black) or \
                        (current_player == 2 and not self.player_is_black)
        
        if not is_player_turn:
            QMessageBox.information(self, "Не ваш ход", "Сейчас ход бота")
            return
            
        if self.board_widget.pass_move():
            self.consecutive_passes += 1
            
            # Номер хода не увеличиваем при пасе
            move_number = (len(self.move_descriptions) - 1) // 2 + 1
            move_desc = f"{move_number}. Пас (игрок)"
            self.ui.historyList.addItem(move_desc)
            self.ui.historyList.scrollToBottom()
            self.save_snapshot_after_move(move_desc)

            if self.consecutive_passes >= 2:
                self.end_game_by_passes()
            else:
                self.bot_move_timer.start(300)

    def end_game_by_passes(self):
        if self.game_ended:
            return

        self.game_ended = True

        if not os.path.exists(GNUGO_PATH):
            QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
            self.game_finished.emit()
            return

        if not gnugo.check_gnugo_available(GNUGO_PATH):
            QMessageBox.critical(
                self, 
                "Ошибка GNU Go", 
                "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
            )
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

        dialog = QProgressDialog("Анализируем позицию с помощью GNU Go...", None, 0, 0, self)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.show()

        self.analysis_task = self.GnuGoAnalysisTask(sgf, self.board_size, GNUGO_PATH)
        self.analysis_task.finished.connect(lambda result: self._on_analysis_finished(result, dialog))
        self.analysis_task.error.connect(lambda e: self._on_analysis_error(e, dialog))
        self.analysis_task.start()

    def _on_analysis_finished(self, winner, dialog):
        dialog.close()
        
        if winner == 1:
            winner_text = "Черные"
            is_player_win = (winner == 1 and self.player_is_black) or (winner == 2 and not self.player_is_black)
        elif winner == 2:
            winner_text = "Белые"
            is_player_win = (winner == 1 and self.player_is_black) or (winner == 2 and not self.player_is_black)
        elif winner == 0:
            winner_text = "Ничья"
            is_player_win = False
        else:
            winner_text = "Не определен"
            is_player_win = False
        
        if is_player_win and winner != 0:
            message = f"Победитель: {winner_text}! Поздравляем, вы выиграли!"
        elif winner != 0:
            message = f"Победитель: {winner_text}! Победил бот."
        else:
            message = f"Игра окончена. Результат: {winner_text}"
        
        QMessageBox.information(self, "Игра окончена", message)
        self.game_finished.emit()

    def _on_analysis_error(self, exception, dialog):
        dialog.close()
        QMessageBox.critical(
            self, 
            "Ошибка GNU Go", 
            "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
        )
        self.game_finished.emit()

    def resign(self):
        if self.game_ended or self.is_bot_thinking or self.gnugo_error_occurred:
            return
            
        reply = QMessageBox.question(self, "Сдаться",
                                   "Вы уверены, что хотите сдаться?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.game_ended = True 
            QMessageBox.information(self, "Игра окончена", "Вы сдались. Победил бот!")
            self.game_finished.emit()