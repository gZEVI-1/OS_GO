import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent   
app_dir = current_dir.parent                  
sys.path.insert(0, str(app_dir))

from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal
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
        self.player_color = player_color
        self.board_size = board_size
        self.time_settings = time_settings
        self.visual_settings = visual_settings

        self.ui = Ui_main()
        self.ui.setupUi(self)

        # --- Состояние игры ---
        self.game_started = False
        self.game_ended = False
        self.consecutive_passes = 0
        self.is_navigating = False

        # --- История и навигация ---
        self.board_snapshots = []
        self.current_snapshot_index = -1
        self.move_descriptions = []
        self.pending_move_desc = None

        # --- Таймеры ---
        self.black_timer = None
        self.white_timer = None
        self.no_time_limit = self.time_settings.get('no_time_limit', False)
        self.setup_timers()

        # --- Доска ---
        self.board_widget = self.ui.boardWidget
        self.board_widget.set_board_size(self.board_size)
        self.board_widget.set_flipped(self.player_color == "white")
        self.board_widget.show_legal_moves = self.visual_settings.get('show_legal_moves', False)
        self.board_widget.cell_clicked.connect(self.on_board_click)

        # --- Чат ---
        self._setup_chat()
        if hasattr(self.ui, 'buttonChat'):
            self.ui.buttonChat.setVisible(False)

        # --- Кнопки ---
        def _connect_btn(name, handler):
            btn = getattr(self.ui, name, None)
            if btn is not None and hasattr(btn, 'clicked'):
                btn.clicked.connect(handler)

        _connect_btn('buttonPass', self.on_pass)
        _connect_btn('buttonResign', self.on_resign)
        _connect_btn('buttonPrevMove', self.prev_move)
        _connect_btn('buttonNextMove', self.next_move)
        _connect_btn('buttonChat', self.on_chat_button)

        self.ui.timerPlayer.setText("00:00")
        self.ui.timerOpponent.setText("00:00")

        # --- Кнопка выхода из лобби ---
        self.btn_leave_lobby = QPushButton("Выйти из лобби")
        self.btn_leave_lobby.clicked.connect(self.leave_lobby)
        layout = getattr(self.ui, 'verticalLayout', None)
        if layout is not None:
            layout.addWidget(self.btn_leave_lobby)
        else:
            self.layout().addWidget(self.btn_leave_lobby)

        # --- Сигналы клиента ---
        self.client.game_started.connect(self.on_game_started)
        self.client.game_state_changed.connect(self.on_game_state)
        self.client.game_over.connect(self.on_game_over)
        self.client.chat_message.connect(self.on_chat_message)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error)
        self.client.move_received.connect(self.on_move_received)

        if self.client.last_game_started_payload is not None:
            self.on_game_started(self.client.last_game_started_payload)

        self.setWindowTitle(f"Сетевая игра — {self.player_name} ({self.player_color})")
        self.update_nav_buttons()

    # ==================== ТАЙМЕРЫ ====================
    def setup_timers(self):
        if self.no_time_limit:
            self.ui.timerPlayer.setText("--:--")
            self.ui.timerOpponent.setText("--:--")
            logger.debug("Таймеры отключены (no_time_limit)")
            return

        main_time = self.time_settings.get('main_time', 600)
        self.black_timer = GameTimer(1, main_time, self, no_time_limit=False)
        self.white_timer = GameTimer(2, main_time, self, no_time_limit=False)

        # Исправление: подключаем сигнал с проверкой наличия аргументов
        self.black_timer.time_changed.connect(lambda *args: self.update_timer_display('black', args[0] if args else 0))
        self.white_timer.time_changed.connect(lambda *args: self.update_timer_display('white', args[0] if args else 0))
        self.black_timer.time_expired.connect(lambda: self.on_time_expired('black'))
        self.white_timer.time_expired.connect(lambda: self.on_time_expired('white'))
        logger.debug(f"Таймеры созданы: main_time={main_time}")

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
                logger.debug("Запущен таймер чёрных")
        else:
            if self.white_timer and not self.white_timer.is_running:
                if self.black_timer:
                    self.black_timer.stop()
                self.white_timer.start()
                logger.debug("Запущен таймер белых")

    def stop_timers(self):
        if self.black_timer:
            self.black_timer.stop()
        if self.white_timer:
            self.white_timer.stop()
        logger.debug("Таймеры остановлены")

    def on_time_expired(self, color: str):
        if self.game_ended:
            return
        self.game_ended = True
        self.stop_timers()
        winner = 'white' if color == 'black' else 'black'
        QMessageBox.information(self, "Время вышло",
                                f"{'Чёрные' if color=='black' else 'Белые'} превысили лимит. Победили {winner}.")
        self.client.send_resign()

    # ==================== ЛОББИ / ЧАТ ====================
    def leave_lobby(self):
        if not self.game_started and self.client and self.client.room_id:
            self.client.leave_room()
            self.game_finished.emit()

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

    def on_chat_message(self, sender: str, text: str):
        self.ui.chatLog.append(f"<{sender}> {text}")

    # ==================== ИГРОВЫЕ СОБЫТИЯ ====================
    def on_game_started(self, payload: dict):
        logger.debug(f"on_game_started: {payload}")
        self.game_started = True
        self.game_ended = False
        self.consecutive_passes = 0

        size = payload.get("board_size", 19)
        self.board_size = size
        self.board_widget.set_board_size(size)

        self.board_widget.setEnabled(True)
        for btn_name in ('buttonPass', 'buttonResign'):
            btn = getattr(self.ui, btn_name, None)
            if btn:
                btn.setEnabled(True)
        self.btn_leave_lobby.setVisible(False)

        self.board_snapshots = []
        self.move_descriptions = []
        self.ui.historyList.clear()
        self.current_snapshot_index = -1

        initial_state = payload.get('initial_state', {})
        board_array = initial_state.get('board', [[0]*size for _ in range(size)])
        self.board_widget.set_board_state(board_array)
        self.save_initial_snapshot()

        current = initial_state.get('current_player', 'black')
        logger.debug(f"Первый игрок: {current}")
        self.start_timer_for_current_player(current)

    def on_game_state(self, state: GameDisplayState):
        logger.debug(f"on_game_state: move_number={state.move_number}, current={state.current_player}, my_turn={state.is_my_turn}")
        if not self.game_started or self.is_navigating:
            return

        self.board_widget.set_board_state(state.board_array, state.last_move)
        self.start_timer_for_current_player(state.current_player)

        if self.pending_move_desc is not None:
            self.save_snapshot_after_move(self.pending_move_desc, state)
            self.pending_move_desc = None
            self.update_nav_buttons()

    def on_move_received(self, move: dict):
        logger.debug(f"on_move_received: {move}")
        if self.is_navigating:
            return

        if not move.get("is_pass"):
            self.consecutive_passes = 0
        else:
            self.consecutive_passes += 1

        move_number = (len(self.move_descriptions)) // 2 + 1
        color_name = "Чёрные" if move.get("color") == "black" else "Белые"
        if move.get("is_pass"):
            desc = f"{move_number}. {color_name}: пас"
        else:
            x = move.get("x", -1)
            y = move.get("y", -1)
            col_letter = chr(65 + x)
            desc = f"{move_number}. {color_name}: {col_letter}{y + 1}"

        self.ui.historyList.addItem(desc)
        self.ui.historyList.scrollToBottom()
        self.move_descriptions.append(desc)

        self.pending_move_desc = desc

        if self.consecutive_passes >= 2:
            self.end_game_by_passes()

    def on_game_over(self, winner: str, result: str, sgf: str):
        logger.debug(f"on_game_over: winner={winner}, result={result}")
        self.game_ended = True
        self.stop_timers()
        winner_text = "Чёрные" if winner == "black" else "Белые" if winner == "white" else winner
        QMessageBox.information(self, "Игра окончена",
                                f"Победитель: {winner_text}\n{result}")
        self.game_finished.emit()

    def on_disconnected(self):
        if not self.game_ended:
            QMessageBox.warning(self, "Соединение", "Потеряно соединение с сервером")
            self.game_finished.emit()

    def on_error(self, code: str, message: str):
        QMessageBox.critical(self, f"Ошибка {code}", message)

    # ==================== ДЕЙСТВИЯ ИГРОКА ====================
    def on_board_click(self, row, col):
        logger.debug(f"Клик по доске: row={row}, col={col}")
        if not self.game_started or self.game_ended:
            return
        state = self.client.get_display_state()
        if state is not None and not getattr(state, 'is_my_turn', True):
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

    # ==================== ДВОЙНОЙ ПАС ====================
    def end_game_by_passes(self):
        if self.game_ended:
            return
        self.game_ended = True
        self.stop_timers()
        QMessageBox.information(self, "Игра окончена", "Два паса подряд. Игра завершена.")
        self.client.send_resign()

    # ==================== НАВИГАЦИЯ ПО ХОДАМ ====================
    def create_snapshot(self, state: GameDisplayState):
        return {
            'board_state': [row[:] for row in state.board_array],
            'current_player': state.current_player,
            'last_move': state.last_move,
            'captures': dict(state.captures)
        }

    def save_initial_snapshot(self):
        state = self.client.get_display_state()
        if state:
            snapshot = self.create_snapshot(state)
            self.board_snapshots = [snapshot]
            self.move_descriptions = ["Начало партии"]
            self.current_snapshot_index = 0
            self.ui.historyList.clear()
            self.ui.historyList.addItem("Начало партии")
            logger.debug("Сохранён начальный снимок")
        else:
            self.board_snapshots = []
            self.move_descriptions = []
            self.current_snapshot_index = -1

    def save_snapshot_after_move(self, move_description, state: GameDisplayState):
        if self.is_navigating:
            return
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self.board_snapshots = self.board_snapshots[:self.current_snapshot_index + 1]
            self.move_descriptions = self.move_descriptions[:self.current_snapshot_index + 1]
            self.ui.historyList.clear()
            for desc in self.move_descriptions:
                self.ui.historyList.addItem(desc)

        snapshot = self.create_snapshot(state)
        self.board_snapshots.append(snapshot)
        self.move_descriptions.append(move_description)
        self.current_snapshot_index = len(self.board_snapshots) - 1
        self.update_nav_buttons()
        logger.debug(f"Сохранён снимок после хода: {move_description}, индекс={self.current_snapshot_index}")

    def restore_snapshot(self, index):
        if not (0 <= index < len(self.board_snapshots)):
            return False
        snapshot = self.board_snapshots[index]
        self.board_widget.set_board_state(snapshot['board_state'], snapshot.get('last_move'))
        self.board_widget.update()
        logger.debug(f"Восстановлен снимок {index}")
        return True

    def update_history_selection(self, snapshot_index):
        if snapshot_index > 0:
            history_index = snapshot_index - 1
            if 0 <= history_index < self.ui.historyList.count():
                self.ui.historyList.setCurrentRow(history_index)
        else:
            self.ui.historyList.clearSelection()

    def update_nav_buttons(self):
        btn_prev = getattr(self.ui, 'buttonPrevMove', None)
        btn_next = getattr(self.ui, 'buttonNextMove', None)
        if btn_prev:
            btn_prev.setEnabled(self.current_snapshot_index > 0)
        if btn_next:
            btn_next.setEnabled(self.current_snapshot_index < len(self.board_snapshots) - 1)
        logger.debug(f"Кнопки навигации: prev={btn_prev.isEnabled() if btn_prev else False}, next={btn_next.isEnabled() if btn_next else False}")

    def jump_to_latest(self):
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.is_navigating = True
            self.current_snapshot_index = len(self.board_snapshots) - 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_nav_buttons()
            self.update_history_selection(self.current_snapshot_index)

    def prev_move(self):
        if self.current_snapshot_index > 0:
            self.is_navigating = True
            self.current_snapshot_index -= 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_nav_buttons()
            self.update_history_selection(self.current_snapshot_index)

    def next_move(self):
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self.is_navigating = True
            self.current_snapshot_index += 1
            self.restore_snapshot(self.current_snapshot_index)
            self.is_navigating = False
            self.update_nav_buttons()
            self.update_history_selection(self.current_snapshot_index)

    def closeEvent(self, event: QCloseEvent):
        if self.client and self.client.room_id:
            self.client.leave_room()
        self.game_finished.emit()
        event.accept()