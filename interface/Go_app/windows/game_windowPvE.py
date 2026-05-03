import sys
import os
import subprocess
from copy import deepcopy
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QThread, Signal, QTimer

from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent.parent

sys.path.append(str(root_path / "scripts"))
import go_engine as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(str(root_path / "interface" / "Go_app"))
sys.path.append(str(root_path / "interface" / "Go_app" / "katago")) 
from KataGoAdapter import KataGoGameAnalyzer, KataGoAnalysisResult
from windows.base_window import BaseWindow
from windows.profile_window import ProfileWindow
from generated.ui_game_windowPvE import Ui_main
import GnuGo_Analyzer as gnugo

GNUGO_PATH = os.path.join(root_path, "bot", "gnugo-3.8", "gnugo.exe")


class GnuGoEngine:
    
    def __init__(self, board_size):
        self.process = None
        self.board_size = board_size
        
    def start(self):
        try:
            self.process = subprocess.Popen(
                [GNUGO_PATH, "--mode", "gtp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Инициализация
            self._send_command(f"boardsize {self.board_size}")
            self._send_command("clear_board")
            self._send_command("komi 6.5")
            
            return True
        except Exception as e:
            print(f"Ошибка запуска GNU Go: {e}")
            return False
    
    def _send_command(self, cmd):
        if not self.process:
            return 
        
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        
        lines = []
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            line = line.rstrip("\n")
            lines.append(line)
            if line == "":
                break
        
        return "\n".join(lines)
    
    def play_move(self, color, x, y, is_pass=False):
        if is_pass:
            cmd = f"play {color} pass"
        else:
            # Преобразуем координаты в GTP формат (без буквы I)
            if x < 8:
                letter = chr(65 + x)
            else:
                letter = chr(66 + x)
            gtp_y = y + 1
            cmd = f"play {color} {letter}{gtp_y}"
        
        return self._send_command(cmd)
    
    def get_move(self, color):
        cmd = f"genmove {color}"
        response = self._send_command(cmd)
        
        # Парсим ответ
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('='):
                move_str = line[1:].strip()
                
                if move_str == 'pass':
                    return (-1, -1, True)
                
                if move_str and len(move_str) >= 2:
                    letter = move_str[0]
                    try:
                        y = int(move_str[1:]) - 1
                        
                        if letter <= 'H':
                            x = ord(letter) - ord('A')
                        else:
                            x = ord(letter) - ord('A') - 1
                        
                        return (x, y, False)
                    except:
                        pass
        
        return (-1, -1, True)
    
    def stop(self):
        if self.process:
            try:
                self._send_command("quit")
            except:
                pass
            self.process.terminate()
            self.process = None


class BotMoveThread(QThread):
    move_ready = Signal(int, int, bool) 
    error = Signal(str)
    
    def __init__(self, gnugo_engine, color):
        super().__init__()
        self.gnugo_engine = gnugo_engine
        self.color = color  
        
    def run(self):
        try:
            x, y, is_pass = self.gnugo_engine.get_move(self.color)
            self.move_ready.emit(x, y, is_pass)
        except Exception as e:
            self.error.emit(str(e))


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
                winner = gnugo.get_winner(self.sgf, self.board_size)
                self.finished.emit(winner)
            except Exception as e:
                self.error.emit(e)


    def __init__(self, navigation, core_api=None, settings=None):
        super().__init__(navigation)
        
        self.game_settings = settings or {
            'board_size': 9,
            'player_is_black': True,
            'visual': {'show_legal_moves': True},
            'time': {'no_time_limit': True}
        }
        
        self.board_size = self.game_settings['board_size']
        self.player_is_black = self.game_settings['player_is_black']
        
        if self.player_is_black:
            self.player_gtp = 'B'
            self.bot_gtp = 'W'
        else:
            self.player_gtp = 'W'
            self.bot_gtp = 'B'
        
        # Базовые параметры
        self.consecutive_passes = 0
        self.game_ended = False
        self.winner = None
        self.is_navigating = False
        self.is_bot_thinking = False
        self.gnugo_engine = None
        
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
        
        # Настройка навигации
        self.board_snapshots = []
        self.current_snapshot_index = -1
        self.move_descriptions = []
        
        # Данные игрока
        self.player_data = {
            'name': 'Игрок', 'rating': 1600, 'wins': 42, 'losses': 17,
            'country': 'Россия', 'avatar_path': None
        }
        
        # Настройка UI для PvE
        self.ui.timerPlayer.hide()
        self.ui.timerOpponent.hide()

        # Данные бота (только для отображения имени, профиль не открывается)
        self.bot_data = {
            'name': 'GNU Go Bot', 'rating': 2000, 'wins': 100, 'losses': 50,
            'country': 'AI', 'avatar_path': None
        }

        # Настройка имен с цветом
        if self.player_is_black:
            self.ui.playerName.setText(f"{self.player_data['name']} (Черные)")
            self.ui.opponentName.setText(f"{self.bot_data['name']} (Белые)")
        else:
            self.ui.playerName.setText(f"{self.player_data['name']} (Белые)")
            self.ui.opponentName.setText(f"{self.bot_data['name']} (Черные)")
        
        self.ui.playerAvatar.clicked.connect(self.show_player_profile)
        
        
        self.ui.buttonPass.clicked.connect(self.pass_move)
        self.ui.buttonResign.clicked.connect(self.resign)
        self.ui.buttonPrevMove.clicked.connect(self.prev_move)
        self.ui.buttonNextMove.clicked.connect(self.next_move)
        
        self.setWindowTitle(f"Игра с ботом GNU Go {self.board_size}×{self.board_size}")
        self.save_initial_snapshot()
        
        # Запускаем GNU Go процесс
        if not self.start_gnugo_engine():
            return
        
        # Если бот играет первым
        if not self.player_is_black:
            QTimer.singleShot(500, self.make_bot_move)
    
    def start_gnugo_engine(self):
        self.gnugo_engine = GnuGoEngine(self.board_size)
        if not self.gnugo_engine.start():
            QMessageBox.critical(
                self,
                "Ошибка GNU Go",
                "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
            )
            self.game_ended = True
            self.game_finished.emit()
            return False
        return True
    
    def send_move_to_gnugo(self, x, y, is_pass):
        if self.gnugo_engine:
            color = self.player_gtp
            self.gnugo_engine.play_move(color, x, y, is_pass)
    
    def update_language(self):
        # Обновляем заголовок окна
        self.setWindowTitle(f"{self.settings.get_text('game_title')} vs Bot {self.board_size}×{self.board_size}")
        
        # Обновляем текст на кнопках
        self.ui.buttonPass.setText(self.settings.get_text("pass_button"))
        self.ui.buttonResign.setText(self.settings.get_text("resign_button"))
        
        # Обновляем имена с учетом языка
        black_text = self.settings.get_text("black")
        white_text = self.settings.get_text("white")
        
        if self.player_is_black:
            self.ui.playerName.setText(f"{self.player_data['name']} ({black_text})")
            self.ui.opponentName.setText(f"{self.bot_data['name']} ({white_text})")
        else:
            self.ui.playerName.setText(f"{self.player_data['name']} ({white_text})")
            self.ui.opponentName.setText(f"{self.bot_data['name']} ({black_text})")
    def make_bot_move(self):
        if self.game_ended or self.is_bot_thinking:
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
        
        self.bot_thread = BotMoveThread(self.gnugo_engine, self.bot_gtp)
        self.bot_thread.move_ready.connect(self.on_bot_move_ready)
        self.bot_thread.error.connect(self.on_bot_error)
        self.bot_thread.start()
    
    def on_bot_move_ready(self, x, y, is_pass):
        self.is_bot_thinking = False
        self.ui.buttonPass.setEnabled(True)
        self.ui.buttonResign.setEnabled(True)
        
        if self.game_ended:
            return
        
        if is_pass:
            self.bot_pass_move()
        else:
            success = self.board_widget.request_move(y, x)  # row=y, col=x
            if not success:
                self.bot_pass_move()
    
    def on_bot_error(self, error_msg):
        self.is_bot_thinking = False
        self.ui.buttonPass.setEnabled(True)
        self.ui.buttonResign.setEnabled(True)
        
        if not self.game_ended:
            self.game_ended = True
            QMessageBox.critical(
                self,
                "Ошибка GNU Go",
                "Ошибка GNU Go. Сейчас мы занимаемся решением этой проблемы."
            )
            self.game_finished.emit()
    
    def on_cell_clicked(self, row, col):
        if self.game_ended or self.is_bot_thinking:
            return
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.jump_to_latest()
        
        current_player = self.board_widget.current_player
        is_player_turn = (current_player == 1 and self.player_is_black) or \
                        (current_player == 2 and not self.player_is_black)
        
        if is_player_turn:
            self.board_widget.request_move(row, col)
    
    def on_move_made(self, row, col, player):
        if self.game_ended:
            return
        
        # Отправляем ход в GNU Go
        self.send_move_to_gnugo(col, row, False)  # x=col, y=row
        
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
        
        if self.core_api.is_game_over():
            self.end_game_by_passes()
            return
        
        # Ход бота
        if not self.game_ended and is_player_move:
            QTimer.singleShot(300, self.make_bot_move)
    
    def pass_move(self):
        if self.game_ended or self.is_bot_thinking:
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
            self.send_move_to_gnugo(-1, -1, True)
            
            self.consecutive_passes += 1
            
            move_number = (len(self.move_descriptions) - 1) // 2 + 1
            move_desc = f"{move_number}. Пас (игрок)"
            self.ui.historyList.addItem(move_desc)
            self.ui.historyList.scrollToBottom()
            self.save_snapshot_after_move(move_desc)
            
            if self.consecutive_passes >= 2 or self.core_api.is_game_over():
                self.end_game_by_passes()
            else:
                QTimer.singleShot(300, self.make_bot_move)
    
    def bot_pass_move(self):
        if self.board_widget.pass_move():
            self.consecutive_passes += 1
            
            move_number = (len(self.move_descriptions) - 1) // 2 + 1
            move_desc = f"{move_number}. Пас (бот)"
            self.ui.historyList.addItem(move_desc)
            self.ui.historyList.scrollToBottom()
            self.save_snapshot_after_move(move_desc)
            
            if self.consecutive_passes >= 2 or self.core_api.is_game_over():
                self.end_game_by_passes()
    
    def end_game_by_passes(self):
        if self.game_ended:
            return
        
        self.game_ended = True
        
        # Останавливаем GNU Go
        if self.gnugo_engine:
            self.gnugo_engine.stop()
        
        # Анализ через GNU Go
        if not os.path.exists(GNUGO_PATH):
            QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
            self.game_finished.emit()
            return
        
        sgf = self.core_api.get_sgf()
        if not sgf or len(sgf) < 30:
            QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
            self.game_finished.emit()
            return
        
        dialog = QProgressDialog("Анализируем позицию...", None, 0, 0, self)
        dialog.setWindowModality(Qt.WindowModal)
        dialog.show()
        
        self.analysis_task = self.GnuGoAnalysisTask(sgf, self.board_size, GNUGO_PATH)
        self.analysis_task.finished.connect(lambda result: self.on_analysis_finished(result, dialog))
        self.analysis_task.error.connect(lambda e: self.on_analysis_error(e, dialog))
        self.analysis_task.start()

    def on_analysis_finished(self, winner, dialog):
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
    
    def on_analysis_error(self, exception, dialog):
        dialog.close()
        QMessageBox.warning(self, "Ошибка анализа", f"Ошибка при анализе партии.\n{exception}")
        self.game_finished.emit()
    

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
    # Методы навигации
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