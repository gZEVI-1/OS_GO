"""
OS-GO Network Client — PySide6-Ready Edition
============================================
Асинхронный клиент для сетевой игры в Го.
Спроектирован для интеграции с PySide6 через QObject-обёртку.

Ключевые изменения для GUI:
- Все колбэки можно безопасно заменить на pyqtSignal из Qt-обёртки
- Убрано дублирование методов
- Добавлен thread-safe доступ к состоянию
- Добавлены хелперы для GUI-рендеринга
"""
import asyncio
import json
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.protocol import State

from protocol import Message, MessageType, GameAction, RoomInfo 
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core_adapter import GameSession, PlayerType
from output_interface import GameDisplayState
import go_engine as go

logger = logging.getLogger("GoClient")


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    IN_ROOM = "in_room"
    PLAYING = "playing"


@dataclass
class GameState:
    """Внутреннее состояние игры. Thread-safe чтение через get_display_state()."""
    board_array: List[List[int]]
    current_player: str
    move_number: int
    passes: int
    last_move: Optional[Dict] = None
    captures: Dict[str, int] = field(default_factory=lambda: {"black": 0, "white": 0})


class NetworkClient:
    """
    Клиент сетевой игры. НЕ наследуется от QObject — для Qt создайте
    QObject-обёртку (см. PySide6_Integration.md).
    
    Все on_* колбэки вызываются из asyncio-цикла. Для Qt-интеграции
    используйте asyncio.run_coroutine_threadsafe() или QMetaObject.invokeMethod.
    """

    def __init__(self, server_url: str, player_name: str):
        self.server_url = server_url
        self.player_name = player_name
        self.ws: Optional[WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED
        self.player_id: Optional[str] = None
        self.player_color: Optional[str] = None
        self.room_id: Optional[str] = None
        self.board_size: int = 19
        self.komi: float = 6.5
        self.rules: str = "japanese"

        # --- Thread-safe состояние ---
        self._lock = threading.RLock()
        self._game_state: Optional[GameState] = None
        self._move_history: List[Dict[str, Any]] = []
        self._last_sgf: Optional[str] = None

        # --- Колбэки (вызываются из asyncio loop) ---
        # Для PySide6: в обёртке замените эти колбэки на emit сигналов
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_room_list: Optional[Callable[[List[RoomInfo]], None]] = None
        self.on_room_joined: Optional[Callable[[str, str], None]] = None
        self.on_room_update: Optional[Callable[[Dict], None]] = None
        self.on_game_started: Optional[Callable[[Dict], None]] = None
        self.on_move_received: Optional[Callable[[Dict], None]] = None
        self.on_game_state_update: Optional[Callable[[GameState], None]] = None
        self.on_game_over: Optional[Callable[[str, str, Optional[str]], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        self.on_player_joined: Optional[Callable[[List[Dict]], None]] = None
        self.on_player_left: Optional[Callable[[str], None]] = None
        self.on_chat_message: Optional[Callable[[str, str], None]] = None
        self.on_undo_request: Optional[Callable[[str], None]] = None
        self.on_undo_response: Optional[Callable[[bool], None]] = None

        self._receive_task: Optional[asyncio.Task] = None
        self._state_event = asyncio.Event()
        self._state_event.set()

        self.local_session: Optional[GameSession] = None

    # --- Thread-safe accessors для GUI ---

    def get_display_state(self) -> Optional[GameDisplayState]:
        """Thread-safe получение состояния для рендеринга GUI."""
        with self._lock:
            if not self._game_state:
                return None
            return GameDisplayState(
                board_size=self.board_size,
                board_array=[row[:] for row in self._game_state.board_array],  # копия
                current_player=self._game_state.current_player,
                move_number=self._game_state.move_number,
                passes=self._game_state.passes,
                last_move=self._game_state.last_move,
                captures=dict(self._game_state.captures),
                player_color=self.player_color,
                is_my_turn=self._is_my_turn_unlocked(),
                mode="network"
            )

    def get_move_history(self) -> List[Dict[str, Any]]:
        """Thread-safe копия истории ходов."""
        with self._lock:
            return list(self._move_history)

    def get_connection_state(self) -> ConnectionState:
        """Thread-safe получение состояния подключения."""
        with self._lock:
            return self.state

    def _is_connected(self) -> bool:
        if self.ws is None:
            return False
        return self.ws.state == State.OPEN

    def _is_my_turn_unlocked(self) -> bool:
        if not self._game_state or not self.player_color:
            return False
        return self._game_state.current_player == self.player_color

    def is_my_turn(self) -> bool:
        """Thread-safe проверка хода."""
        with self._lock:
            return self._is_my_turn_unlocked()

    # --- Сетевые методы ---

    async def connect(self) -> bool:
        try:
            with self._lock:
                self.state = ConnectionState.CONNECTING
            self.ws = await websockets.connect(self.server_url)
            with self._lock:
                self.state = ConnectionState.CONNECTED
            await self._send(Message.connect(self.player_name))
            await asyncio.sleep(0.1)
            await self._send(Message.lobby_ready())

            self._receive_task = asyncio.create_task(self._receive_loop())
            if self.on_connected:
                self.on_connected()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            with self._lock:
                self.state = ConnectionState.DISCONNECTED
            return False

    async def disconnect(self):
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        with self._lock:
            self.state = ConnectionState.DISCONNECTED
        if self.on_disconnected:
            self.on_disconnected()

    async def create_room(self, name: str, board_size: int = 19,
                          password: Optional[str] = None,
                          komi: float = 6.5, rules: str = "japanese") -> bool:
        if self.get_connection_state() != ConnectionState.CONNECTED:
            return False
        await self._send(Message.room_create(
            name=name, board_size=board_size,
            password=password, komi=komi, rules=rules
        ))
        return True

    async def join_room(self, room_id: str, password: Optional[str] = None) -> bool:
        if self.get_connection_state() != ConnectionState.CONNECTED:
            return False
        await self._send(Message.room_join(room_id, password))
        return True

    async def leave_room(self):
        if self.room_id:
            await self._send(Message(MessageType.ROOM_LEAVE))
            with self._lock:
                self.room_id = None
                self.state = ConnectionState.CONNECTED

    async def set_ready(self, is_ready: bool = True):
        await self._send(Message.room_ready(is_ready))

    async def send_move(self, x: int, y: int) -> bool:
        with self._lock:
            if self.state != ConnectionState.PLAYING or not self._game_state:
                return False
            if self._game_state.current_player != self.player_color:
                return False
            move_num = self._game_state.move_number
        await self._send(Message.game_move(x, y, move_num))
        return True

    async def send_pass(self) -> bool:
        with self._lock:
            if self.state != ConnectionState.PLAYING or not self._game_state:
                return False
            move_num = self._game_state.move_number
        await self._send(Message.game_pass(move_num))
        return True

    async def send_resign(self):
        await self._send(Message(MessageType.GAME_RESIGN))

    async def request_undo(self):
        with self._lock:
            if not self._game_state:
                return
            move_num = self._game_state.move_number
        await self._send(Message.undo_request(move_num))

    async def send_chat(self, text: str):
        await self._send(Message.game_chat(self.player_name, text))

    async def _send(self, message: Message):
        if self._is_connected():
            try:
                await self.ws.send(message.to_json())
            except Exception as e:
                logger.error(f"Send error: {e}")
        else:
            logger.warning("Cannot send: not connected")

    async def _receive_loop(self):
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Receive error: {e}")
        finally:
            with self._lock:
                self.state = ConnectionState.DISCONNECTED

    async def _handle_message(self, data: str):
        try:
            msg = Message.from_json(data)
            handler = getattr(self, f"_on_{msg.type.value}", None)
            if handler:
                await handler(msg)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    # --- Обработчики сообщений ---

    async def _on_error(self, msg: Message):
        code = msg.payload.get("code", "UNKNOWN")
        message = msg.payload.get("message", "Unknown error")
        if self.on_error:
            self.on_error(code, message)

    async def _on_room_list(self, msg: Message):
        rooms_data = msg.payload.get("rooms", [])
        rooms = [RoomInfo(**r) for r in rooms_data]
        if self.on_room_list:
            self.on_room_list(rooms)

    async def _on_room_join(self, msg: Message):
        if msg.payload.get("success"):
            with self._lock:
                self.room_id = msg.payload.get("room_id")
                self.player_color = msg.payload.get("player_color")
                self.state = ConnectionState.IN_ROOM
            if self.on_room_joined:
                self.on_room_joined(self.room_id, self.player_color)
        else:
            if self.on_error:
                self.on_error("JOIN_FAILED", msg.payload.get("message", "Unknown"))

    async def _on_room_update(self, msg: Message):
        if self.on_room_update:
            self.on_room_update(msg.payload)
        event = msg.payload.get("event", "")
        if event == "player_joined" and self.on_player_joined:
            self.on_player_joined(msg.payload.get("players", []))
        elif event == "player_left" and self.on_player_left:
            self.on_player_left(msg.payload.get("player_name", "unknown"))

    async def _on_game_start(self, msg: Message):
        with self._lock:
            self.state = ConnectionState.PLAYING
            self.board_size = msg.payload.get("board_size", 19)
            self.komi = msg.payload.get("komi", 6.5)
            self.rules = msg.payload.get("rules", "japanese")
            self._move_history = []
            self._last_sgf = None
            initial = msg.payload.get("initial_state", {})
            self._game_state = GameState(
                board_array=initial.get("board", []),
                current_player=initial.get("current_player", "black"),
                move_number=initial.get("move_number", 1),
                passes=initial.get("passes", 0),
                captures=initial.get("captures", {"black": 0, "white": 0})
            )
        self._state_event.set()
        if self.on_game_started:
            self.on_game_started(msg.payload)

    async def _on_game_state(self, msg: Message):
        payload = msg.payload
        with self._lock:
            self._game_state = GameState(
                board_array=payload.get("board", []),
                current_player=payload.get("current_player", "black"),
                move_number=payload.get("move_number", 1),
                passes=payload.get("passes", 0),
                last_move=payload.get("last_move"),
                captures=payload.get("captures", {"black": 0, "white": 0})
            )
        self._state_event.set()
        if self.on_game_state_update:
            self.on_game_state_update(self._game_state)

    async def _on_game_move(self, msg: Message):
        move = msg.payload.get("move", {})
        if move:
            with self._lock:
                self._move_history.append(move)
                if self._game_state:
                    self._game_state.last_move = move
        if self.on_move_received:
            self.on_move_received(move)

    async def _on_game_pass(self, msg: Message):
        move = msg.payload.get("move", {})
        if move:
            with self._lock:
                self._move_history.append(move)
                if self._game_state:
                    self._game_state.last_move = move
        # Сервер присылает отдельный game_state после pass
        if self.on_move_received:
            self.on_move_received(move)

    async def _on_game_over(self, msg: Message):
        with self._lock:
            self.state = ConnectionState.IN_ROOM
            self._last_sgf = msg.payload.get("sgf")
        self._state_event.set()
        winner = msg.payload.get("winner", "")
        result = msg.payload.get("result", "")
        sgf = msg.payload.get("sgf")
        if self.on_game_over:
            self.on_game_over(winner, result, sgf)

    async def _on_game_chat(self, msg: Message):
        if self.on_chat_message:
            self.on_chat_message(
                msg.payload.get("sender", ""),
                msg.payload.get("text", "")
            )

    async def _on_game_undo_request(self, msg: Message):
        if self.on_undo_request:
            self.on_undo_request(msg.payload.get("requester", ""))

    async def _on_game_undo_response(self, msg: Message):
        if self.on_undo_response:
            self.on_undo_response(msg.payload.get("accepted", False))

    # --- SGF и сохранение ---

    def get_sgf(self) -> str:
        """Формирует SGF из накопленной истории. Thread-safe."""
        with self._lock:
            if self._last_sgf:
                return self._last_sgf
            if not self._move_history:
                return ""
            sgf = f"(;GM[1]FF[4]SZ[{self.board_size}]KM[{self.komi}]AP[OS-GO:Network:1.0]\\n"
            for move in self._move_history:
                color = "B" if move.get("color") == "black" else "W"
                if move.get("is_pass"):
                    sgf += f";{color}[]"
                else:
                    x = move.get("x", -1)
                    y = move.get("y", -1)
                    if 0 <= x < self.board_size and 0 <= y < self.board_size:
                        x_char = chr(ord('a') + x)
                        y_char = chr(ord('a') + y)
                        sgf += f";{color}[{x_char}{y_char}]"
            sgf += ")"
            return sgf

    def save_game(self, filepath: Optional[str] = None) -> Optional[str]:
        """Сохраняет текущую партию в SGF. Thread-safe. Возвращает путь к файлу."""
        sgf = self.get_sgf()
        if not sgf:
            return None
        if filepath is None:
            try:
                import config as cfg
                filepath = cfg.get_sgf_path(game_mode="network")
            except Exception:
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                filepath = os.path.join(base, "games", "network", f"game_{id(self)}.sgf")
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(sgf)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save SGF: {e}")
            return None

    # --- Хелперы для GUI ---

    def get_local_board(self) -> Optional[go.Board]:
        """Создаёт go.Board из текущего состояния. Полезно для KataGo-анализа."""
        with self._lock:
            if not self._game_state:
                return None
            board = go.Board(self.board_size)
            array = self._game_state.board_array
            for y in range(self.board_size):
                for x in range(self.board_size):
                    val = array[y][x] if y < len(array) and x < len(array[y]) else 0
                    if val == 1:
                        board.add_stone(x, y, go.Color.Black)
                    elif val == 2:
                        board.add_stone(x, y, go.Color.White)
            return board

    def format_move(self, x: int, y: int) -> str:
        """Форматирует координаты в человекочитаемый вид (например, D4)."""
        from core_adapter import CoordinateUtils
        return CoordinateUtils.format_move(x, y)

    async def wait_for_state_change(self, timeout: float = 5.0) -> bool:
        """Блокируется до получения GAME_STATE или GAME_OVER. 
        В GUI НЕ используйте напрямую — замените на сигнал on_game_state_update."""
        self._state_event.clear()
        try:
            await asyncio.wait_for(self._state_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def get_last_move_as_object(self) -> Optional[go.Move]:
        """Возвращает последний ход как go.Move для движка."""
        with self._lock:
            if not self._move_history:
                return None
            last = self._move_history[-1]
        return GameAction.dict_to_move(last)

