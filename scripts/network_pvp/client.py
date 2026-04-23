"""
OS-GO Network Client
====================

Асинхронный WebSocket клиент для сетевой игры в Го.
Абстрагирует сетевое взаимодействие, предоставляя callback-интерфейс.

Использование:
    from client import NetworkClient, ClientEvent

    client = NetworkClient("ws://localhost:8765", "PlayerName")
    client.on_move_received = lambda move: print(f"Opponent moved: {move}")
    await client.connect()
    await client.join_room("room_id")
    await client.send_move(3, 4)

Зависимости:
    websockets>=16.0, go_engine
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.protocol import State  # websockets 16.0+

from protocol import Message, MessageType, GameAction, RoomInfo

# Добавляем путь к core_adapter
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
    """Текущее состояние игры (синхронизированное с сервером)"""
    board_array: List[List[int]]
    current_player: str  # "black" или "white"
    move_number: int
    passes: int
    last_move: Optional[Dict] = None
    captures: Dict[str, int] = None

    def __post_init__(self):
        if self.captures is None:
            self.captures = {"black": 0, "white": 0}


class NetworkClient:
    """
    Клиент сетевой игры в Го.

    Предоставляет событийный интерфейс через callback'и:
        - on_connected: подключение установлено
        - on_room_joined: вход в комнату выполнен
        - on_game_started: игра началась
        - on_move_received: получен ход противника
        - on_game_state_update: обновление состояния доски
        - on_game_over: игра окончена
        - on_error: ошибка от сервера
        - on_player_joined/left: изменение состава комнаты
        - on_chat_message: сообщение в чате
        - on_undo_request: запрос отмены хода от противника
    """

    def __init__(self, server_url: str, player_name: str):
        self.server_url = server_url
        self.player_name = player_name

        self.ws: Optional[WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED
        self.player_id: Optional[str] = None
        self.player_color: Optional[str] = None
        self.room_id: Optional[str] = None

        # Текущее состояние игры
        self.game_state: Optional[GameState] = None
        self.board_size: int = 19

        # Callback'и (переопределяются пользователем)
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_room_list: Optional[Callable[[List[RoomInfo]], None]] = None
        self.on_room_joined: Optional[Callable[[str, str], None]] = None  # room_id, color
        self.on_room_update: Optional[Callable[[Dict], None]] = None
        self.on_game_started: Optional[Callable[[Dict], None]] = None
        self.on_move_received: Optional[Callable[[Dict], None]] = None
        self.on_game_state_update: Optional[Callable[[GameState], None]] = None
        self.on_game_over: Optional[Callable[[str, str], None]] = None  # winner, result
        self.on_error: Optional[Callable[[str, str], None]] = None  # code, message
        self.on_player_joined: Optional[Callable[[Dict], None]] = None
        self.on_player_left: Optional[Callable[[str], None]] = None
        self.on_chat_message: Optional[Callable[[str, str], None]] = None  # sender, text
        self.on_undo_request: Optional[Callable[[str], None]] = None  # requester_name
        self.on_undo_response: Optional[Callable[[bool], None]] = None

        # Внутренние
        self._receive_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._response_futures: Dict[str, asyncio.Future] = {}

    # ==================== ПОДКЛЮЧЕНИЕ ====================

    def _is_connected(self) -> bool:
        """Проверяет, открыто ли соединение (совместимо с websockets 16.0+)"""
        if self.ws is None:
            return False
        # websockets 16.0+: используем state вместо open
        return self.ws.state == State.OPEN

    async def connect(self) -> bool:
        """Устанавливает соединение с сервером"""
        try:
            self.state = ConnectionState.CONNECTING
            self.ws = await websockets.connect(self.server_url)
            self.state = ConnectionState.CONNECTED

            # Отправляем приветствие
            await self._send(Message.connect(self.player_name))

            # Запускаем обработчик входящих сообщений
            self._receive_task = asyncio.create_task(self._receive_loop())

            if self.on_connected:
                self.on_connected()

            logger.info(f"Connected to {self.server_url}")
            return True

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.DISCONNECTED
            return False

    async def disconnect(self):
        """Закрывает соединение"""
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        self.state = ConnectionState.DISCONNECTED
        if self.on_disconnected:
            self.on_disconnected()

    # ==================== ЛОББИ ====================

    async def create_room(self, name: str, board_size: int = 19,
                         password: Optional[str] = None,
                         komi: float = 6.5,
                         rules: str = "japanese") -> bool:
        """Создает новую игровую комнату"""
        if self.state != ConnectionState.CONNECTED:
            return False

        await self._send(Message.room_create(
            name=name, board_size=board_size,
            password=password, komi=komi, rules=rules
        ))
        return True

    async def join_room(self, room_id: str, password: Optional[str] = None) -> bool:
        """Входит в существующую комнату"""
        if self.state != ConnectionState.CONNECTED:
            return False

        await self._send(Message.room_join(room_id, password))
        return True

    async def leave_room(self):
        """Покидает текущую комнату"""
        if self.room_id:
            await self._send(Message(MessageType.ROOM_LEAVE))
            self.room_id = None
            self.state = ConnectionState.CONNECTED

    async def set_ready(self, is_ready: bool = True):
        """Устанавливает статус готовности"""
        await self._send(Message.room_ready(is_ready))

    # ==================== ИГРОВЫЕ ДЕЙСТВИЯ ====================

    async def send_move(self, x: int, y: int) -> bool:
        """
        Отправляет ход на сервер.
        Проверяет, что сейчас ход текущего игрока.
        """
        if self.state != ConnectionState.PLAYING or not self.game_state:
            return False

        # Проверяем очередь
        if self.game_state.current_player != self.player_color:
            return False

        move_number = self.game_state.move_number
        await self._send(Message.game_move(x, y, move_number))
        return True

    async def send_pass(self) -> bool:
        """Отправляет пас"""
        if self.state != ConnectionState.PLAYING or not self.game_state:
            return False

        move_number = self.game_state.move_number
        await self._send(Message.game_pass(move_number))
        return True

    async def send_resign(self):
        """Сдается"""
        await self._send(Message(MessageType.GAME_RESIGN))

    async def request_undo(self):
        """Запрашивает отмену последнего хода"""
        if not self.game_state:
            return
        await self._send(Message.undo_request(self.game_state.move_number))

    async def respond_undo(self, accepted: bool):
        """Отвечает на запрос отмены"""
        await self._send(Message.undo_response(accepted))

    async def send_chat(self, text: str):
        """Отправляет сообщение в чат"""
        await self._send(Message.game_chat(self.player_name, text))

    # ==================== ВНУТРЕННИЕ МЕТОДЫ ====================

    async def _send(self, message: Message):
        """Отправляет сообщение на сервер"""
        if self._is_connected():
            try:
                await self.ws.send(message.to_json())
            except Exception as e:
                logger.error(f"Send error: {e}")
                # Можно добавить логику переподключения здесь
        else:
            logger.warning("Cannot send: not connected")

    async def _receive_loop(self):
        """Основной цикл получения сообщений"""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
        except Exception as e:
            logger.error(f"Receive error: {e}")
        finally:
            self.state = ConnectionState.DISCONNECTED

    async def _handle_message(self, data: str):
        """Обработка входящих сообщений"""
        try:
            msg = Message.from_json(data)
            handler = getattr(self, f"_on_{msg.type.value}", None)

            if handler:
                await handler(msg)
            else:
                logger.warning(f"No handler for {msg.type.value}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    # --- Обработчики событий ---

    async def _on_error(self, msg: Message):
        code = msg.payload.get("code", "UNKNOWN")
        message = msg.payload.get("message", "Unknown error")
        logger.error(f"Server error: [{code}] {message}")
        if self.on_error:
            self.on_error(code, message)

    async def _on_room_list(self, msg: Message):
        rooms_data = msg.payload.get("rooms", [])
        rooms = [RoomInfo(**r) for r in rooms_data]
        if self.on_room_list:
            self.on_room_list(rooms)

    async def _on_room_join(self, msg: Message):
        if msg.payload.get("success"):
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
            players = msg.payload.get("players", [])
            self.on_player_joined(players)
        elif event == "player_left" and self.on_player_left:
            players = msg.payload.get("players", [])
            # Определяем кто ушел по разнице списков
            self.on_player_left("unknown")

    async def _on_game_start(self, msg: Message):
        self.state = ConnectionState.PLAYING
        self.board_size = msg.payload.get("board_size", 19)

        # Инициализируем локальное состояние
        initial = msg.payload.get("initial_state", {})
        self.game_state = GameState(
            board_array=initial.get("board", []),
            current_player=initial.get("current_player", "black"),
            move_number=initial.get("move_number", 1),
            passes=initial.get("passes", 0),
            captures=initial.get("captures", {"black": 0, "white": 0})
        )

        if self.on_game_started:
            self.on_game_started(msg.payload)

    async def _on_game_state(self, msg: Message):
        payload = msg.payload
        self.game_state = GameState(
            board_array=payload.get("board", []),
            current_player=payload.get("current_player", "black"),
            move_number=payload.get("move_number", 1),
            passes=payload.get("passes", 0),
            last_move=payload.get("last_move"),
            captures=payload.get("captures", {"black": 0, "white": 0})
        )

        if self.on_game_state_update:
            self.on_game_state_update(self.game_state)

    async def _on_game_move(self, msg: Message):
        if self.on_move_received:
            self.on_move_received(msg.payload.get("move", {}))

    async def _on_game_pass(self, msg: Message):
        # Обновляем состояние
        await self._on_game_state(Message(MessageType.GAME_STATE, msg.payload.get("board_state", {})))
        if self.on_move_received:
            self.on_move_received(msg.payload.get("move", {}))

    async def _on_game_over(self, msg: Message):
        self.state = ConnectionState.IN_ROOM  # Возвращаемся в комнату
        winner = msg.payload.get("winner", "")
        result = msg.payload.get("result", "")

        if self.on_game_over:
            self.on_game_over(winner, result)

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

    # ==================== УТИЛИТЫ ====================

    def is_my_turn(self) -> bool:
        """Проверяет, сейчас ли ход текущего игрока"""
        if not self.game_state or not self.player_color:
            return False
        return self.game_state.current_player == self.player_color

    def get_local_board(self) -> Optional[go.Board]:
        """
        Создает локальный go_engine.Board из текущего сетевого состояния.
        Полезно для локальной валидации или отображения.
        """
        if not self.game_state:
            return None

        board = go.Board(self.board_size)
        array = self.game_state.board_array

        for y in range(self.board_size):
            for x in range(self.board_size):
                val = array[y][x] if y < len(array) and x < len(array[y]) else 0
                if val == 1:
                    board.add_stone(x, y, go.Color.Black)
                elif val == 2:
                    board.add_stone(x, y, go.Color.White)

        return board

    def format_move(self, x: int, y: int) -> str:
        """Форматирует координаты в человекочитаемый вид (например, D4)"""
        from core_adapter import CoordinateUtils
        return CoordinateUtils.format_move(x, y)