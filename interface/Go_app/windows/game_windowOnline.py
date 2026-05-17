import sys
import logging
from pathlib import Path
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).resolve().parent   
app_dir = current_dir.parent                  
sys.path.insert(0, str(app_dir))

from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QProgressDialog
from PySide6.QtCore import Qt, Signal, QTimer, QThread
from PySide6.QtGui import QCloseEvent
from windows.app_settings import AppSettings

from windows.base_window import BaseWindow
from generated.ui_game_windowOnline import Ui_main
from output_interface import GameDisplayState
import GnuGo_Analyzer as gnugo

# Путь к GNU Go (измените под вашу структуру проекта)
root_path = Path(__file__).resolve().parent.parent.parent.parent
GNUGO_PATH = os.path.join(root_path, "bot", "gnugo-3.8", "gnugo.exe")


class GameWindowOnline(BaseWindow):
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
                analyzer = gnugo.GnuGoAnalyzer(gnugo_path=self.gnugo_path)
                try:
                    result = analyzer.analyze_sgf(self.sgf, self.board_size)
                finally:
                    analyzer.cleanup()
                self.finished.emit(result)
            except Exception as e:
                self.error.emit(e)

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
        self.settings = AppSettings()

        self.game_started = False
        self.game_ended = False
        self.ended_by_passes = False          # флаг завершения двумя пасами
        self.consecutive_passes = 0
        self.is_navigating = False
        self.last_move_number = 0

        self.board_snapshots = []
        self.current_snapshot_index = -1
        self.move_descriptions = []

        # --- DEBUG & SYNC STATE ---
        self._debug_counter = 0
        self._last_processed_move_number = -1
        self._expected_move_number = 1
        self._processed_state_hashes = set()
        self._move_in_flight = False
        self._pass_in_flight = False
        self._current_player = None
        self._my_turn = False

        # --- Локальные таймеры (QTimer) ---
        self.no_time_limit = self.time_settings.get('no_time_limit', False)
        self.black_time_left = self.time_settings.get('main_time', 600) if not self.no_time_limit else 0
        self.white_time_left = self.time_settings.get('main_time', 600) if not self.no_time_limit else 0
        self.black_timer = None
        self.white_timer = None
        self.setup_local_timers()

        # --- Доска ---
        self.board_widget = self.ui.boardWidget
        self.board_widget.show_last_move_highlight = False
        self.board_widget.set_board_size(self.board_size)
        self.board_widget.set_flipped(self.player_color == "white")
        self.board_widget.show_legal_moves = self.visual_settings.get('show_legal_moves', False)
        self.board_widget.cell_clicked.connect(self.on_board_click)

        # --- Чат ---
        self._setup_chat()
        if hasattr(self.ui, 'buttonChat'):
            self.ui.buttonChat.setVisible(False)

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

        self.btn_leave_lobby = QPushButton(self.settings.get_text("leave_lobby_button"))
        self.btn_leave_lobby.clicked.connect(self.leave_lobby)
        layout = getattr(self.ui, 'verticalLayout', None)
        if layout is not None:
            layout.addWidget(self.btn_leave_lobby)
        else:
            self.layout().addWidget(self.btn_leave_lobby)

        # --- Подключение сигналов клиента ---
        self.client.game_started.connect(self.on_game_started)
        self.client.game_state_changed.connect(self.on_game_state)
        self.client.game_over.connect(self.on_game_over)
        self.client.chat_message.connect(self.on_chat_message)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error)
        self.client.move_received.connect(self.on_move_received)

        if self.client.last_game_started_payload is not None:
            self._debug_print("INIT", "Обнаружен last_game_started_payload, вызываем on_game_started")
            self.on_game_started(self.client.last_game_started_payload)

        self.setWindowTitle(f"{self.settings.get_text('online_game_title')} — {self.player_name} ({self.player_color})")
        self.update_nav_buttons()
        self._debug_print("INIT", f"Инициализация завершена. player_color={self.player_color}, "
                                  f"board_size={self.board_size}, no_time_limit={self.no_time_limit}")

        # --- Анализ ---
        self.analysis_dialog = None
        self.analysis_task = None

    # ==================== DEBUG UTILS ====================
    def _debug_print(self, tag: str, msg: str, data=None):
        self._debug_counter += 1
        prefix = f"[DEBUG #{self._debug_counter:04d}] [{tag}]"
        if data is not None:
            print(f"{prefix} {msg} | DATA: {data}")
        else:
            print(f"{prefix} {msg}")

    def _debug_dump_internal_state(self):
        print("=" * 70)
        print("INTERNAL STATE DUMP:")
        print(f"  game_started:              {self.game_started}")
        print(f"  game_ended:                {self.game_ended}")
        print(f"  ended_by_passes:           {self.ended_by_passes}")
        print(f"  is_navigating:             {self.is_navigating}")
        print(f"  last_move_number:          {self.last_move_number}")
        print(f"  _last_processed_move_num:  {self._last_processed_move_number}")
        print(f"  _expected_move_number:     {self._expected_move_number}")
        print(f"  _current_player:           {self._current_player}")
        print(f"  _my_turn:                  {self._my_turn}")
        print(f"  consecutive_passes:        {self.consecutive_passes}")
        print(f"  _move_in_flight:           {self._move_in_flight}")
        print(f"  _pass_in_flight:           {self._pass_in_flight}")
        print(f"  snapshots_count:           {len(self.board_snapshots)}")
        print(f"  current_snapshot_index:    {self.current_snapshot_index}")
        print(f"  black_time_left:           {self.black_time_left}")
        print(f"  white_time_left:           {self.white_time_left}")
        print(f"  processed_hashes_count:    {len(self._processed_state_hashes)}")
        print("=" * 70)

    def _debug_state_info(self, state):
        if state is None:
            return "None"
        return {
            'move_number': getattr(state, 'move_number', '?'),
            'current_player': getattr(state, 'current_player', '?'),
            'is_my_turn': getattr(state, 'is_my_turn', '?'),
            'last_move': getattr(state, 'last_move', '?'),
            'captures': getattr(state, 'captures', '?'),
        }

    def _state_hash(self, state: GameDisplayState) -> str:
        lm = state.last_move or {}
        lmn = lm.get('move_number', '?')
        return (f"MN{state.move_number}:LMN{lmn}:CP{state.current_player}:"
                f"X{lm.get('x','?')}:Y{lm.get('y','?')}:P{lm.get('is_pass','?')}")

    # ==================== TURN CALCULATION ====================
    def _calc_next_player_from_move(self, move: dict) -> str:
        """Вычисляет следующего игрока по цвету ПОСЛЕДНЕГО хода."""
        if not move:
            return self._current_player or 'black'
        last_color = move.get('color')
        if last_color is None:
            last_color = 'white' if self._current_player == 'black' else 'black'
        return 'white' if last_color == 'black' else 'black'

    def _update_my_turn(self, next_player: str):
        """Обновляет внутренний флаг очереди хода."""
        old = self._my_turn
        self._current_player = next_player
        self._my_turn = (next_player == self.player_color)
        if old != self._my_turn:
            self._debug_print("TURN", f"_my_turn changed: {old} -> {self._my_turn} "
                                      f"(current={next_player}, me={self.player_color})")

    # ==================== ЛОКАЛЬНЫЕ ТАЙМЕРЫ ====================
    def setup_local_timers(self):
        self._debug_print("TIMER", "setup_local_timers called")
        if self.no_time_limit:
            self.ui.timerPlayer.setText("--:--")
            self.ui.timerOpponent.setText("--:--")
            return

        self.black_timer = QTimer(self)
        self.white_timer = QTimer(self)
        self.black_timer.timeout.connect(lambda: self._update_timer('black'))
        self.white_timer.timeout.connect(lambda: self._update_timer('white'))
        self.black_timer.setInterval(1000)
        self.white_timer.setInterval(1000)

        self._update_timer_display('black', self.black_time_left)
        self._update_timer_display('white', self.white_time_left)

    def _update_timer(self, color):
        if color == 'black':
            if self.black_time_left > 0:
                self.black_time_left -= 1
                self._update_timer_display('black', self.black_time_left)
                if self.black_time_left == 0:
                    self.black_timer.stop()
                    self.on_time_expired('black')
        else:
            if self.white_time_left > 0:
                self.white_time_left -= 1
                self._update_timer_display('white', self.white_time_left)
                if self.white_time_left == 0:
                    self.white_timer.stop()
                    self.on_time_expired('white')

    def _update_timer_display(self, color, seconds):
        minutes = seconds // 60
        secs = seconds % 60
        text = f"{minutes:02d}:{secs:02d}"
        if self.player_color == "white":
            if color == 'white':
                self.ui.timerPlayer.setText(text)
            else:
                self.ui.timerOpponent.setText(text)
        else:
            if color == 'black':
                self.ui.timerPlayer.setText(text)
            else:
                self.ui.timerOpponent.setText(text)

    def start_local_timer_for_player(self, player_color):
        self._debug_print("TIMER", f"start_local_timer_for_player({player_color})", {
            "no_time_limit": self.no_time_limit,
            "game_ended": self.game_ended,
            "game_started": self.game_started
        })
        if self.no_time_limit or self.game_ended or not self.game_started:
            return
        self.black_timer.stop()
        self.white_timer.stop()
        if player_color == 'black':
            if self.black_time_left > 0:
                self.black_timer.start()
                self._debug_print("TIMER", ">>> Таймер ЧЁРНЫХ запущен")
        else:
            if self.white_time_left > 0:
                self.white_timer.start()
                self._debug_print("TIMER", ">>> Таймер БЕЛЫХ запущен")

    def stop_local_timers(self):
        if self.black_timer:
            self.black_timer.stop()
        if self.white_timer:
            self.white_timer.stop()
        self._debug_print("TIMER", "Все таймеры остановлены")

    def on_time_expired(self, color):
        if self.game_ended:
            return
        self.game_ended = True
        self.stop_local_timers()
        winner = 'white' if color == 'black' else 'black'
        player_name = self.settings.get_text("black_color") if color == 'black' else self.settings.get_text("white_color")
        winner_name = self.settings.get_text("white_color") if winner == 'white' else self.settings.get_text("black_color")
        msg = self.settings.get_text("time_expired_message").format(player_name, winner_name)
        QMessageBox.information(self, self.settings.get_text("time_expired_title"), msg)
        self.client.send_resign()

    # ==================== ЛОББИ / ЧАТ ====================
    def leave_lobby(self):
        self._debug_print("LOBBY", "leave_lobby called")
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
        self._debug_print("GAME", "on_game_started", payload)
        self.game_started = True
        self.game_ended = False
        self.ended_by_passes = False
        self.consecutive_passes = 0
        self.is_navigating = False
        self.last_move_number = 0

        self._last_processed_move_number = -1
        self._expected_move_number = 1
        self._move_in_flight = False
        self._pass_in_flight = False
        self._processed_state_hashes.clear()

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

        # Сохраняем начальный снимок (пустая доска, без добавления в список истории)
        self.save_initial_snapshot(board_array, initial_state.get('current_player', 'black'))

        if not self.no_time_limit:
            self.black_time_left = self.time_settings.get('main_time', 600)
            self.white_time_left = self.time_settings.get('main_time', 600)
            self._update_timer_display('black', self.black_time_left)
            self._update_timer_display('white', self.white_time_left)

        self._current_player = initial_state.get('current_player', 'black')
        self._update_my_turn(self._current_player)
        self.start_local_timer_for_player(self._current_player)

    def _make_move_description(self, move: dict, move_number: int) -> str:
        pair_number = (move_number + 1) // 2
        color_name = "Чёрные" if move.get("color") == "black" else "Белые"
        if move.get("is_pass"):
            return f"{pair_number}. {color_name}: пас"
        else:
            x = move.get("x", -1)
            y = move.get("y", -1)
            if x == -1 or y == -1:
                return None
            col_letter = chr(65 + x)
            return f"{pair_number}. {color_name}: {col_letter}{y + 1}"

    def _ensure_not_navigating(self):
        """Если пользователь смотрит историю — сбросить на последний ход."""
        if self.is_navigating or self.current_snapshot_index < len(self.board_snapshots) - 1:
            self._debug_print("NAV", "User was navigating, jumping to latest before processing new move")
            self.jump_to_latest_internal()

    def jump_to_latest_internal(self):
        """Внутренний сброс навигации без лишних side-effects."""
        if self.current_snapshot_index != len(self.board_snapshots) - 1:
            self.is_navigating = False
            self.current_snapshot_index = len(self.board_snapshots) - 1
            self.restore_snapshot(self.current_snapshot_index)
            self.update_nav_buttons()
            self.update_history_selection(self.current_snapshot_index)

    def _exit_navigation_if_needed(self):
        """Если пользователь смотрит историю — возвращаемся к актуальному состоянию и синхронизируем очередь."""
        if self.is_navigating:
            self._debug_print("NAV", "Exiting navigation mode due to user action")
            self.jump_to_latest_internal()
            state = self.client.get_display_state()
            if state:
                self._current_player = state.current_player
                self._my_turn = (state.current_player == self.player_color)
                self.start_local_timer_for_player(self._current_player)

    def _apply_state(self, state: GameDisplayState, move: dict = None, source="unknown") -> bool:
        """
        Применить состояние. 
        move: если передан, используем его для вычисления следующего игрока и номера хода.
        """
        self._debug_print("STATE", f"_apply_state called from [{source}]", {
            "state": self._debug_state_info(state),
            "move": move
        })

        if not state:
            self._debug_print("STATE", "state is None, ignoring")
            return False
        if not self.game_started:
            self._debug_print("STATE", "game not started yet, ignoring")
            return False
        if self.game_ended:
            self._debug_print("STATE", "game already ended, ignoring")
            return False

        move_number = move.get('move_number') if move else None
        if move_number is not None and move_number > self._last_processed_move_number:
            self._ensure_not_navigating()

        state_hash = self._state_hash(state)
        if state_hash in self._processed_state_hashes:
            self._debug_print("STATE", f"DUPLICATE STATE DETECTED (hash={state_hash}), ignoring!")
            return False
        self._processed_state_hashes.add(state_hash)

        self.board_widget.set_board_state(state.board_array, state.last_move)

        # Принудительная синхронизация очереди хода из состояния
        if state.current_player != self._current_player:
            self._debug_print("STATE", f"Force sync current_player: {self._current_player} -> {state.current_player}")
            self._update_my_turn(state.current_player)
            self.start_local_timer_for_player(state.current_player)

        actual_move = move if move else (state.last_move if state.last_move else None)
        actual_move_number = move_number if move_number is not None else (
            state.last_move.get('move_number') if state.last_move else 0
        )

        if actual_move and actual_move_number > self._last_processed_move_number:
            self._debug_print("STATE", f"NEW MOVE DETECTED: {self._last_processed_move_number} -> {actual_move_number}")
            self._last_processed_move_number = actual_move_number
            self._expected_move_number = actual_move_number + 1
            self.last_move_number = state.move_number

            next_player = self._calc_next_player_from_move(actual_move)
            self._update_my_turn(next_player)
            self.start_local_timer_for_player(next_player)

            desc = self._make_move_description(actual_move, actual_move_number)
            if desc and desc not in self.move_descriptions:
                self.ui.historyList.addItem(desc)
                self.ui.historyList.scrollToBottom()
                self.move_descriptions.append(desc)
                self.save_snapshot_after_move(desc, state)
                self.update_nav_buttons()
                self._debug_print("STATE", f"History item added: '{desc}'")

            if actual_move.get("is_pass"):
                self.consecutive_passes += 1
                self._debug_print("PASS", f"Pass registered! consecutive_passes={self.consecutive_passes}")
            else:
                if self.consecutive_passes > 0:
                    self._debug_print("PASS", f"Regular move breaks pass streak, resetting")
                self.consecutive_passes = 0

            if self.consecutive_passes >= 2:
                self._debug_print("PASS", "!!! TWO CONSECUTIVE PASSES DETECTED !!!")
                self.end_game_by_passes()
        else:
            self._debug_print("STATE", f"No new move to process (actual_move_number={actual_move_number}, "
                                       f"processed={self._last_processed_move_number})")
            if self._current_player:
                self.start_local_timer_for_player(self._current_player)

        self._debug_dump_internal_state()
        return True

    def on_game_state(self, state: GameDisplayState):
        self._debug_print("GAME", "on_game_state triggered", self._debug_state_info(state))
        if not self.game_started:
            self._debug_print("GAME", "IGNORED: game not started")
            return
        if self.game_ended:
            self._debug_print("GAME", "IGNORED: game already ended")
            return

        if self._move_in_flight or self._pass_in_flight:
            self._debug_print("GAME", f"Resetting flight flags (move={self._move_in_flight}, pass={self._pass_in_flight})")
            self._move_in_flight = False
            self._pass_in_flight = False

        self._apply_state(state, source="game_state")

    def on_move_received(self, move: dict):
        self._debug_print("MOVE", "on_move_received triggered", move)
        if self.game_ended:
            self._debug_print("MOVE", "IGNORED: game already ended")
            return

        if move.get("is_pass"):
            if self._pass_in_flight:
                self._pass_in_flight = False
                self._debug_print("MOVE", "Pass in flight resolved by server response")
        else:
            if self._move_in_flight:
                self._move_in_flight = False
                self._debug_print("MOVE", "Move in flight resolved by server response")

        client_state = self.client.get_display_state()
        if client_state:
            applied = self._apply_state(client_state, move=move, source="move_received->client_state")
            if not applied:
                self._debug_print("MOVE", "_apply_state rejected the state, will try manual fallback")
                self._manual_process_from_move(move)
        else:
            self._debug_print("MOVE", "client_state is None, using manual fallback")
            self._manual_process_from_move(move)

    def _manual_process_from_move(self, move: dict):
        move_number = move.get('move_number', 0)
        if move_number <= self._last_processed_move_number:
            self._debug_print("MOVE", f"Manual fallback: move {move_number} already processed")
            return

        self._ensure_not_navigating()

        self._last_processed_move_number = move_number
        self._expected_move_number = move_number + 1
        self.last_move_number = move_number + 1

        is_pass = move.get("is_pass", False)
        next_player = self._calc_next_player_from_move(move)
        self._update_my_turn(next_player)
        self.start_local_timer_for_player(next_player)

        desc = self._make_move_description(move, move_number)
        if desc and desc not in self.move_descriptions:
            self.ui.historyList.addItem(desc)
            self.ui.historyList.scrollToBottom()
            self.move_descriptions.append(desc)
            self._debug_print("STATE", f"Manual history item added: '{desc}'")

            state_after = self.client.get_display_state()
            if state_after:
                self.save_snapshot_after_move(desc, state_after)
            else:
                fake_state = type('FakeState', (), {
                    'board_array': self.board_widget.get_board_state(),
                    'current_player': next_player,
                    'last_move': move,
                    'captures': {}
                })()
                self.save_snapshot_after_move(desc, fake_state)

        if is_pass:
            self.consecutive_passes += 1
            self._debug_print("PASS", f"Manual pass count: {self.consecutive_passes}")
        else:
            self.consecutive_passes = 0

        if self.consecutive_passes >= 2:
            self._debug_print("PASS", "!!! TWO CONSECUTIVE PASSES (manual) !!!")
            self.end_game_by_passes()

        self._debug_dump_internal_state()

    def on_game_over(self, winner: str, result: str, sgf: str):
        self._debug_print("GAME", f"on_game_over: winner={winner}, result={result}, sgf_len={len(sgf)}")
        self.game_ended = True
        self._my_turn = False
        self.stop_local_timers()

        if self.ended_by_passes:
            # Запускаем анализ GNU Go
            if not os.path.exists(GNUGO_PATH):
                self._debug_print("ANALYSIS", "GNU Go not found, showing simple message")
                QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
                self.game_finished.emit()
                return

            if not gnugo.check_gnugo_available(GNUGO_PATH):
                self._debug_print("ANALYSIS", "GNU Go check failed")
                QMessageBox.information(self, "Игра окончена", "Два паса! Игра завершена.")
                self.game_finished.emit()
                return

            if not sgf or len(sgf) < 30:
                self._debug_print("ANALYSIS", "SGF too short for analysis")
                QMessageBox.information(
                    self, "Игра окончена",
                    "Игра завершена двумя пасами.\nАнализ недоступен: слишком короткая партия."
                )
                self.game_finished.emit()
                return

            # Показываем диалог анализа
            self.analysis_dialog = QProgressDialog(self.settings.get_text("game_analysis_progress"), None, 0, 0, self)
            self.analysis_dialog.setWindowModality(Qt.WindowModal)
            self.analysis_dialog.setCancelButton(None)                # убираем кнопку
            self.analysis_dialog.rejected.connect(self.cancel_analysis)  # крестик → отмена
            self.analysis_dialog.show()

            self.analysis_task = self.GnuGoAnalysisTask(sgf, self.board_size, GNUGO_PATH)
            self.analysis_task.finished.connect(lambda res: self.on_analysis_finished(res, winner, result))
            self.analysis_task.error.connect(self.on_analysis_error)
            self.analysis_task.start()
        else:
            # Обычное завершение (не двумя пасами)
            winner_text = "Чёрные" if winner == "black" else "Белые" if winner == "white" else winner
            QMessageBox.information(self, "Игра окончена",
                                    f"Победитель: {winner_text}\n{result}")
            self.game_finished.emit()

    def on_disconnected(self):
        self._debug_print("NET", "on_disconnected")
        self._my_turn = False
        if not self.game_ended:
            QMessageBox.warning(self, "Соединение", "Потеряно соединение с сервером")
            self.game_finished.emit()

    def on_error(self, code: str, message: str):
        self._debug_print("ERROR", f"code={code}, message={message}")
        self._move_in_flight = False
        self._pass_in_flight = False
        QMessageBox.critical(self, f"Ошибка {code}", message)

    # ==================== ДЕЙСТВИЯ ИГРОКА ====================
    def on_board_click(self, row, col):
        self._debug_print("INPUT", f"on_board_click(row={row}, col={col})", {
            "game_started": self.game_started,
            "game_ended": self.game_ended,
            "move_in_flight": self._move_in_flight,
            "pass_in_flight": self._pass_in_flight,
            "my_turn": self._my_turn,
            "navigating": self.is_navigating
        })

        self._exit_navigation_if_needed()

        if not self.game_started or self.game_ended:
            self._debug_print("INPUT", "CLICK IGNORED: game not active")
            return
        if self._move_in_flight or self._pass_in_flight:
            self._debug_print("INPUT", "CLICK IGNORED: action already in flight")
            return
        if not self._my_turn:
            self._debug_print("INPUT", "CLICK IGNORED: NOT MY TURN (internal state)")
            return

        self._move_in_flight = True
        self._debug_print("INPUT", f"SENDING MOVE to server: x={col}, y={row}, expected_move={self._expected_move_number}")
        self.client.send_move(row, col) 

    def on_pass(self):
        self._debug_print("INPUT", "on_pass called", {
            "game_started": self.game_started,
            "game_ended": self.game_ended,
            "pass_in_flight": self._pass_in_flight,
            "my_turn": self._my_turn,
            "navigating": self.is_navigating
        })

        self._exit_navigation_if_needed()

        if not self.game_started or self.game_ended:
            self._debug_print("INPUT", "PASS IGNORED: game not active")
            return
        if self._pass_in_flight:
            self._debug_print("INPUT", "PASS IGNORED: already in flight")
            return
        if not self._my_turn:
            self._debug_print("INPUT", "PASS IGNORED: NOT MY TURN (internal state)")
            return

        self._pass_in_flight = True
        self._debug_print("INPUT", f"SENDING PASS to server, expected_move={self._expected_move_number}")
        self.client.send_pass()

    def on_resign(self):
        self._debug_print("INPUT", "on_resign called")
        if not self.game_started or self.game_ended:
            return
        reply = QMessageBox.question(self, self.settings.get_text("resign_title"), self.settings.get_text("resign_confirm_message"))    
        if reply == QMessageBox.Yes:
            self.client.send_resign()

    def end_game_by_passes(self):
        self._debug_print("GAME", "end_game_by_passes() invoked")
        if self.game_ended:
            return
        self.game_ended = True
        self.ended_by_passes = True
        self._my_turn = False
        self.stop_local_timers()
        # Не отправляем resign — сервер сам завершит игру после двух пасов
        self._debug_print("PASS", "Two consecutive passes, waiting for server game_over")

    # ==================== АНАЛИЗ ПОСЛЕ ДВУХ ПАСОВ ====================
    def on_analysis_finished(self, result, winner, result_str):
        if self.analysis_dialog:
            self.analysis_dialog.hide()
            self.analysis_dialog.deleteLater()
            self.analysis_dialog = None

        if result and isinstance(result, dict):
            winner_text = result.get('winner', self.settings.get_text("black_color") if winner == 'black' else self.settings.get_text("white_color"))
            margin = result.get('margin', 0)
            message = self.settings.get_text("winner_label").format(winner_text)
            if margin > 0:
                message += "\n" + self.settings.get_text("margin_label").format(margin)
            QMessageBox.information(self, self.settings.get_text("game_ended"), message)
        else:
            QMessageBox.information(self, self.settings.get_text("game_ended"), self.settings.get_text("two_passes_finished"))
        self.game_finished.emit()
        self.analysis_task = None

    def on_analysis_error(self, exception):
        if self.analysis_dialog:
            self.analysis_dialog.close()
            self.analysis_dialog.deleteLater()
            self.analysis_dialog = None

        QMessageBox.warning(
            self, "Ошибка анализа",
            QMessageBox.warning(self, self.settings.get_text("analysis_error_title"),
                                self.settings.get_text("analysis_error_message").format(exception))
        )
        self.game_finished.emit()
        self.analysis_task = None

    def cancel_analysis(self):
        if self.analysis_task and self.analysis_task.isRunning():
            self.analysis_task.terminate()
            self.analysis_task.wait(1000)
            self.analysis_task = None
        if self.analysis_dialog:
            self.analysis_dialog.close()
            self.analysis_dialog = None
        self.game_finished.emit()

    # ==================== НАВИГАЦИЯ ПО ХОДАМ ====================
    def create_snapshot(self, state: GameDisplayState):
        return {
            'board_state': [row[:] for row in state.board_array],
            'current_player': state.current_player,
            'last_move': state.last_move,
            'captures': dict(state.captures)
        }

    def save_initial_snapshot(self, board_array, current_player):
        """Сохраняет начальное состояние (пустая доска) без добавления в список истории."""
        self._debug_print("SNAP", "save_initial_snapshot")
        snapshot = {
            'board_state': [row[:] for row in board_array],
            'current_player': current_player,
            'last_move': None,
            'captures': {}
        }
        self.board_snapshots = [snapshot]
        self.move_descriptions = []  # список описаний ходов начинается пустым
        self.current_snapshot_index = 0
        self.ui.historyList.clear()  # не добавляем "Начало партии"
        self._debug_print("SNAP", "Initial snapshot saved (no history entry)")

    def save_snapshot_after_move(self, move_description, state: GameDisplayState):
        self._debug_print("SNAP", f"save_snapshot_after_move: '{move_description}'")
        if self.is_navigating:
            self._debug_print("SNAP", "IGNORED: is_navigating=True — this should not happen!")
            return
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self._debug_print("SNAP", "Truncating forward history")
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
        self._debug_print("SNAP", f"Snapshot saved at index {self.current_snapshot_index}, total={len(self.board_snapshots)}")

    def restore_snapshot(self, index):
        self._debug_print("SNAP", f"restore_snapshot({index})")
        if not (0 <= index < len(self.board_snapshots)):
            self._debug_print("SNAP", f"Invalid index {index}, range is 0..{len(self.board_snapshots)-1}")
            return False
        snapshot = self.board_snapshots[index]
        self.board_widget.set_board_state(snapshot['board_state'], snapshot.get('last_move'))
        self.board_widget.update()
        self._debug_print("SNAP", f"Restored snapshot {index} successfully")
        return True

    def update_history_selection(self, snapshot_index):
        # При snapshot_index == 0 (начальное состояние) снимаем выделение в списке
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

    def jump_to_latest(self):
        self._debug_print("NAV", "jump_to_latest")
        self.jump_to_latest_internal()

    def prev_move(self):
        self._debug_print("NAV", f"prev_move from index {self.current_snapshot_index}")
        if self.current_snapshot_index > 0:
            self.is_navigating = True
            self.current_snapshot_index -= 1
            self.restore_snapshot(self.current_snapshot_index)
            self.update_nav_buttons()
            self.update_history_selection(self.current_snapshot_index)

    def next_move(self):
        self._debug_print("NAV", f"next_move from index {self.current_snapshot_index}")
        if self.current_snapshot_index < len(self.board_snapshots) - 1:
            self.current_snapshot_index += 1
            self.restore_snapshot(self.current_snapshot_index)
            if self.current_snapshot_index == len(self.board_snapshots) - 1:
                self.is_navigating = False
                self._debug_print("NAV", "Reached latest, exiting navigation mode")
            self.update_nav_buttons()
            self.update_history_selection(self.current_snapshot_index)

    def closeEvent(self, event: QCloseEvent):
        self._debug_print("LIFE", "closeEvent triggered")
        # Отменяем анализ, если он выполняется
        if hasattr(self, 'analysis_task') and self.analysis_task and self.analysis_task.isRunning():
            self.analysis_task.terminate()
            self.analysis_task.wait(1000)
        if self.client and self.client.room_id:
            self.client.leave_room()
        self.game_finished.emit()
        event.accept()