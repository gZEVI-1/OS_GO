import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent   
app_dir = current_dir.parent                  
sys.path.insert(0, str(app_dir))
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCloseEvent

from windows.base_window import BaseWindow
from generated.ui_game_windowOnline import Ui_main
from output_interface import GameDisplayState
from game_timer import GameTimer

class GameWindowOnline(BaseWindow):
    game_finished = Signal()

    def __init__(self, navigation, client, player_name: str, player_color: str,
                 board_size: int, time_settings: dict, visual_settings: dict):
        super().__init__(navigation)
        self.client = client
        self.player_name = player_name
        self.player_color = player_color          # "black" или "white"
        self.board_size = board_size
        self.time_settings = time_settings        # { 'no_time_limit': bool, 'main_time': int, 'byoyomi': int }
        self.visual_settings = visual_settings    # { 'show_legal_moves': bool }

        self.ui = Ui_main()
        self.ui.setupUi(self)

        # --- Состояние игры ---
        self.game_started = False
        self.game_ended = False
        self.consecutive_passes = 0
        self.is_navigating = False

        # --- История и навигация ---
        self.move_history = []          # список строк для historyList
        self.board_snapshots = []       # снимки состояния доски для навигации
        self.current_snapshot_index = -1
        self.move_descriptions = []     

        # --- Таймеры ---
        self.black_timer = None
        self.white_timer = None
        self.no_time_limit = self.time_settings.get('no_time_limit', False)
        self.setup_timers()

        # --- Настройка доски ---
        self.board_widget = self.ui.boardWidget
        self.board_widget.set_board_size(self.board_size)
        self.board_widget.set_flipped(self.player_color == "white")
        self.board_widget.show_legal_moves = self.visual_settings.get('show_legal_moves', True)
        self.board_widget.cell_clicked.connect(self.on_board_click)

        self._setup_chat()
        if hasattr(self.ui, 'buttonChat'):
            self.ui.buttonChat.setVisible(False)

        self.ui.buttonPass.clicked.connect(self.on_pass)
        self.ui.buttonResign.clicked.connect(self.on_resign)
        self.ui.buttonPrevMove.clicked.connect(self.prev_move)
        self.ui.buttonNextMove.clicked.connect(self.next_move)
        self.ui.buttonChat.clicked.connect(self.on_chat_button)

        self.game_started = False   

        # --- Изначальное состояние (ожидание) ---
        self.ui.timerPlayer.setText("00:00")
        self.ui.timerOpponent.setText("00:00")
        self.board_widget.setEnabled(False)   # доска неактивна
        self.ui.buttonPass.setEnabled(False)
        self.ui.buttonResign.setEnabled(False)

        # --- Кнопка выхода из лобби ---
        self.btn_leave_lobby = QPushButton("Выйти из лобби")
        self.btn_leave_lobby.clicked.connect(self.leave_lobby)
        self.ui.verticalLayout.addWidget(self.btn_leave_lobby)

        self.client.game_started.connect(self.on_game_started)
        self.client.game_state_changed.connect(self.on_game_state)
        self.client.game_over.connect(self.on_game_over)
        self.client.chat_message.connect(self.on_chat_message)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error)
        self.client.move_received.connect(self.on_move_received)

        # --- Заголовок ---
        self.setWindowTitle(f"Сетевая игра — {self.player_name} ({self.player_color})")
        self.update_nav_buttons()

    # ========== Таймеры ==========
    def setup_timers(self):
        if self.no_time_limit:
            self.ui.timerPlayer.setText("--:--")
            self.ui.timerOpponent.setText("--:--")
            return

        main_time = self.time_settings.get('main_time', 600)   # секунды
        # byoyomi пока не используется (можно добавить позже в логику GameTimer)

        self.black_timer = GameTimer(1, main_time, self, no_time_limit=False)
        self.white_timer = GameTimer(2, main_time, self, no_time_limit=False)

        self.black_timer.time_changed.connect(lambda seconds: self.update_timer_display('black', seconds))
        self.white_timer.time_changed.connect(lambda seconds: self.update_timer_display('white', seconds))
        self.black_timer.time_expired.connect(lambda: self.on_time_expired('black'))
        self.white_timer.time_expired.connect(lambda: self.on_time_expired('white'))

    def update_timer_display(self, color: str, seconds: int):
        minutes = seconds // 60
        secs = seconds % 60
        text = f"{minutes:02d}:{secs:02d}"
        if color == 'black':
            self.ui.timerPlayer.setText(text)
        else:
            self.ui.timerOpponent.setText(text)

    def start_timer_for_current_player(self, current_player: str):
        if self.no_time_limit or not self.game_started or self.game_ended:
            return
        if current_player == 'black':
            if self.black_timer and not self.black_timer.is_running:
                if self.white_timer:
                    self.white_timer.stop()
                self.black_timer.start()
        else:
            if self.white_timer and not self.white_timer.is_running:
                if self.black_timer:
                    self.black_timer.stop()
                self.white_timer.start()

    def stop_timers(self):
        if self.black_timer:
            self.black_timer.stop()
        if self.white_timer:
            self.white_timer.stop()

    def on_time_expired(self, color: str):
        if self.game_ended:
            return
        self.game_ended = True
        self.stop_timers()
        winner = 'white' if color == 'black' else 'black'
        QMessageBox.information(self, "Время вышло", f"{color} превысил лимит времени. Победили {winner}.")
        self.client.send_resign()

    def on_game_started(self, payload: dict):
        self.game_started = True
        # Активируем интерфейс
        self.board_widget.setEnabled(True)
        self.ui.buttonPass.setEnabled(True)
        self.ui.buttonResign.setEnabled(True)
        self.btn_leave_lobby.setVisible(False) 

    def leave_lobby(self):
        if not self.game_started and self.client and self.client.room_id:
            self.client.leave_room()
            self.game_finished.emit()

    def closeEvent(self, event):
        if not self.game_started and self.client and self.client.room_id:
            self.client.leave_room()
        self.game_finished.emit()
        event.accept()   
    def _setup_chat(self):
        if hasattr(self.ui, 'chatLog') and hasattr(self.ui, 'chatInput'):
            self.ui.chatSend = getattr(self.ui, 'chatSend', None)
            if self.ui.chatSend:
                self.ui.chatSend.clicked.connect(self.send_chat)
            else:
                self._create_chat_widgets()
            self.ui.chatInput.returnPressed.connect(self.send_chat)
            return
        self._create_chat_widgets()

    def _create_chat_widgets(self):
        chat_group = QVBoxLayout()
        self.ui.chatLog = QTextEdit()
        self.ui.chatLog.setReadOnly(True)
        self.ui.chatLog.setMaximumHeight(150)
        self.ui.chatInput = QLineEdit()
        self.ui.chatInput.setPlaceholderText("Введите сообщение...")
        self.ui.chatInput.returnPressed.connect(self.send_chat)
        self.ui.chatSend = QPushButton("Отправить")
        self.ui.chatSend.clicked.connect(self.send_chat)
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.ui.chatInput)
        input_layout.addWidget(self.ui.chatSend)
        chat_group.addWidget(self.ui.chatLog)
        chat_group.addLayout(input_layout)
        self.ui.verticalLayout.insertLayout(1, chat_group)

    def send_chat(self):
        text = self.ui.chatInput.text().strip()
        if text:
            self.client.send_chat(text)
            self.ui.chatInput.clear()

    def on_chat_button(self):
        self.send_chat()

    def on_game_started(self, payload: dict):
        self.game_started = True
        self.game_ended = False
        self.consecutive_passes = 0
        # Очищаем историю
        self.move_history = []
        self.board_snapshots = []
        self.move_descriptions = []
        self.ui.historyList.clear()
        self.current_snapshot_index = -1
        # Сохраняем начальное состояние
        initial_state = payload.get('initial_state', {})
        board_array = initial_state.get('board', [[0]*self.board_size for _ in range(self.board_size)])
        self.board_widget.set_board_state(board_array)
        self.save_initial_snapshot()
        # Запускаем таймер для текущего игрока
        current = initial_state.get('current_player', 'black')
        self.start_timer_for_current_player(current)

    def on_game_state(self, state: GameDisplayState):
        if not self.game_started or self.is_navigating:
            return
        # Обновляем доску
        self.board_widget.set_board_state(state.board_array, state.last_move)
        # Обновляем захваты
        self.ui.timerPlayer.setText(f"⚫ {state.captures.get('black',0)}")
        self.ui.timerOpponent.setText(f"⚪ {state.captures.get('white',0)}")
        # Запускаем таймер текущего игрока
        self.start_timer_for_current_player(state.current_player)

    def on_move_received(self, move: dict):
        if self.is_navigating:
            return
        move_number = len(self.move_history) + 1
        color_name = "Чёрные" if move.get("color") == "black" else "Белые"
        if move.get("is_pass"):
            desc = f"{move_number}. {color_name}: пас"
            self.consecutive_passes += 1
        else:
            x = move.get("x", -1) + 1
            y = move.get("y", -1) + 1
            desc = f"{move_number}. {color_name}: {chr(64+x)}{y}"
            self.consecutive_passes = 0

        self.move_history.append(desc)
        self.ui.historyList.addItem(desc)
        self.ui.historyList.scrollToBottom()

        # Сохраняем снимок доски
        current_state = self.client.get_display_state()
        if current_state:
            snapshot = {
                'board_state': [row[:] for row in current_state.board_array],
                'current_player': current_state.current_player,
                'last_move': current_state.last_move,
                'captures': dict(current_state.captures)
            }
            self.board_snapshots.append(snapshot)
            self.move_descriptions.append(desc)
            self.current_snapshot_index = len(self.board_snapshots) - 1

        self.update_nav_buttons()

    def on_game_over(self, winner: str, result: str, sgf: str):
        self.game_ended = True
        self.stop_timers()
        winner_text = "Чёрные" if winner == "black" else "Белые" if winner == "white" else winner
        QMessageBox.information(self, "Игра окончена", f"Победитель: {winner_text}\n{result}")
        self.game_finished.emit()

    def on_chat_message(self, sender: str, text: str):
        self.ui.chatLog.append(f"<{sender}> {text}")

    def on_disconnected(self):
        if not self.game_ended:
            QMessageBox.warning(self, "Соединение", "Потеряно соединение с сервером")
            self.game_finished.emit()

    def on_error(self, code: str, message: str):
        QMessageBox.critical(self, f"Ошибка {code}", message)

    def on_board_click(self, row, col):
        if not self.game_started or self.game_ended:
            return
        self.client.send_move(col, row)

    def on_pass(self):
        if not self.game_started or self.game_ended:
            return
        self.client.send_pass()

    def on_resign(self):
        if not self.game_started or self.game_ended:
            return
        reply = QMessageBox.question(self, "Сдаться", "Вы уверены?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.client.send_resign()

    def save_initial_snapshot(self):
        state = self.client.get_display_state()
        if state:
            snapshot = {
                'board_state': [row[:] for row in state.board_array],
                'current_player': state.current_player,
                'last_move': state.last_move,
                'captures': dict(state.captures)
            }
            self.board_snapshots = [snapshot]
            self.move_descriptions = ["Начало партии"]
            self.current_snapshot_index = 0
            self.ui.historyList.clear()
            self.ui.historyList.addItem("Начало партии")
        else:
            self.board_snapshots = []
            self.move_descriptions = []
            self.current_snapshot_index = -1

    def restore_snapshot(self, index):
        if not (0 <= index < len(self.board_snapshots)):
            return False
        snapshot = self.board_snapshots[index]
        self.board_widget.set_board_state(snapshot['board_state'], snapshot.get('last_move'))
        caps = snapshot.get('captures', {'black':0, 'white':0})
        self.ui.timerPlayer.setText(f"⚫ {caps.get('black',0)}")
        self.ui.timerOpponent.setText(f"⚪ {caps.get('white',0)}")
        return True

    def update_nav_buttons(self):
        self.ui.buttonPrevMove.setEnabled(self.current_snapshot_index > 0)
        self.ui.buttonNextMove.setEnabled(self.current_snapshot_index < len(self.board_snapshots) - 1)

    def prev_move(self):
        if self.current_snapshot_index > 0:
            self.is_navigating = True
            self.current_snapshot_index -= 1
            self.restore_snapshot(self.current_snapshot_index)
            if self.current_snapshot_index >= 0 and self.current_snapshot_index < len(self.move_descriptions):
                self.ui.historyList.setCurrentRow(self.current_snapshot_index)
            self.is_navigating = False
            self.update_nav_buttons()

    def next_move(self):
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self.is_navigating = True
            self.current_snapshot_index += 1
            self.restore_snapshot(self.current_snapshot_index)
            if self.current_snapshot_index < len(self.move_descriptions):
                self.ui.historyList.setCurrentRow(self.current_snapshot_index)
            self.is_navigating = False
            self.update_nav_buttons()

    def closeEvent(self, event: QCloseEvent):
        if self.client and self.client.room_id:
            self.client.leave_room()
        self.game_finished.emit()
        event.accept()