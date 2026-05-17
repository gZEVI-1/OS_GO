
import asyncio
import threading
import logging
from typing import Optional, List

from PySide6.QtCore import QObject, Signal, QThread

import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent 
project_root = current_dir.parent.parent.parent   
network_pvp_path = project_root / "scripts" / "network_pvp"
sys.path.insert(0, str(network_pvp_path))

from client import NetworkClient, ConnectionState
from protocol import Message, RoomInfo
from output_interface import GameDisplayState

logger = logging.getLogger("QtNetworkClient")

class AsyncioThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = True
        self._ready = threading.Event()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._ready.set()
        logger.info("AsyncioThread: loop started")
        self.loop.run_forever()
        logger.info("AsyncioThread: loop stopped")

    def stop(self):
        self._running = False
        self._ready.set()
        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception as e:
                logger.warning(f"Error stopping loop: {e}")
        self.wait(3000)

    def submit(self, coro):
        ready = self._ready.wait(timeout=5.0)
        if not ready:
            logger.error("AsyncioThread не стартовал за 5 сек!")
            return None
        if self.loop and self._running and not self.loop.is_closed():
            try:
                return asyncio.run_coroutine_threadsafe(coro, self.loop)
            except Exception as e:
                logger.error(f"submit error: {e}")
        return None


class QtNetworkClient(QObject):
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str, str)          # code, message
    room_list_received = Signal(list)          # List[RoomInfo]
    room_joined = Signal(str, str)             # room_id, color
    room_updated = Signal(dict)                # payload
    game_started = Signal(dict)                # payload
    game_state_changed = Signal(object)        # GameDisplayState
    move_received = Signal(dict)               # move dict
    game_over = Signal(str, str, str)          # winner, result, sgf
    player_joined = Signal(list)               # players list
    player_left = Signal(str)                  # player_name
    chat_message = Signal(str, str)            # sender, text
    undo_requested = Signal(str)               # requester name
    undo_responded = Signal(bool)              # accepted

    def __init__(self, server_url: str, player_name: str, parent=None):
        super().__init__(parent)
        self._client = NetworkClient(server_url, player_name)
        self._thread = AsyncioThread(self)
        self._thread.start()

        self._client.on_connected = lambda: self.connected.emit()
        self._client.on_disconnected = lambda: self.disconnected.emit()
        self._client.on_error = lambda c, m: self.error_occurred.emit(c, m)
        self._client.on_room_list = lambda r: self.room_list_received.emit(r)
        self._client.on_room_joined = lambda rid, col: self.room_joined.emit(rid, col)
        self._client.on_room_update = lambda p: self.room_updated.emit(p)
        self._client.on_game_started = lambda p: self.game_started.emit(p)
        self._client.on_move_received = lambda m: self.move_received.emit(m)
        self._client.on_game_over = lambda w, r, s: self.game_over.emit(w, r, s or "")
        self._client.on_player_joined = lambda p: self.player_joined.emit(p)
        self._client.on_player_left = lambda n: self.player_left.emit(n)
        self._client.on_chat_message = lambda s, t: self.chat_message.emit(s, t)
        self._client.on_undo_request = lambda r: self.undo_requested.emit(r)
        self._client.on_undo_response = lambda a: self.undo_responded.emit(a)
        self._client.on_game_state_update = self._on_state_update

    def _on_state_update(self, _):
        display = self._client.get_display_state()
        if display:
            self.game_state_changed.emit(display)


    def connect_to_server(self):
        """Подключиться к серверу (асинхронно)."""
        self._thread.submit(self._client.connect())

    def disconnect_from_server(self):
        self._thread.submit(self._client.disconnect())

    def refresh_rooms(self):
        """Запросить список комнат."""
        self._thread.submit(self._client._send(Message.lobby_ready()))

    def create_room(self, name: str, board_size: int = 19,
                    password: Optional[str] = None,
                    komi: float = 6.5, rules: str = "japanese"):
        self._thread.submit(self._client.create_room(name, board_size, password, komi, rules))

    def join_room(self, room_id: str, password: Optional[str] = None):
        self._thread.submit(self._client.join_room(room_id, password))

    def leave_room(self):
        self._thread.submit(self._client.leave_room())

    def set_ready(self, ready: bool = True):
        self._thread.submit(self._client.set_ready(ready))

    def send_move(self, x: int, y: int):
        self._thread.submit(self._client.send_move(x, y))

    def send_pass(self):
        self._thread.submit(self._client.send_pass())

    def send_resign(self):
        self._thread.submit(self._client.send_resign())

    def request_undo(self):
        self._thread.submit(self._client.request_undo())

    def respond_undo(self, accepted: bool):
        self._thread.submit(self._client._send(Message.undo_response(accepted)))

    def send_chat(self, text: str):
        self._thread.submit(self._client.send_chat(text))

    def get_display_state(self) -> Optional[GameDisplayState]:
        """Получить текущее состояние для отображения (синхронно)."""
        return self._client.get_display_state()

    def get_sgf(self) -> str:
        return self._client.get_sgf()

    def save_game(self, filepath: Optional[str] = None) -> Optional[str]:
        return self._client.save_game(filepath)

    def shutdown(self):
        self.disconnect_from_server()
        self._thread.stop()

    @property
    def player_name(self) -> str:
        return self._client.player_name

    @property
    def room_id(self) -> Optional[str]:
        return self._client.room_id

    @property
    def player_color(self) -> Optional[str]:
        return self._client.player_color

    @property
    def connection_state(self) -> ConnectionState:
        return self._client.get_connection_state()