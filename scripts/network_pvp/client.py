"""
OS-GO Network Client
"""
import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
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
    board_array: List[List[int]]
    current_player: str
    move_number: int
    passes: int
    last_move: Optional[Dict] = None
    captures: Dict[str, int] = None

    def __post_init__(self):
        if self.captures is None:
            self.captures = {"black": 0, "white": 0}

class NetworkClient:
    def __init__(self, server_url: str, player_name: str):
        self.server_url = server_url
        self.player_name = player_name
        self.ws: Optional[WebSocketClientProtocol] = None 
        self.state = ConnectionState.DISCONNECTED
        self.player_id: Optional[str] = None
        self.player_color: Optional[str] = None
        self.room_id: Optional[str] = None
        self.game_state: Optional[GameState] = None
        self.board_size: int = 19

        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
        self.on_room_list: Optional[Callable[[List[RoomInfo]], None]] = None
        self.on_room_joined: Optional[Callable[[str, str], None]] = None
        self.on_room_update: Optional[Callable[[Dict], None]] = None
        self.on_game_started: Optional[Callable[[Dict], None]] = None
        self.on_move_received: Optional[Callable[[Dict], None]] = None
        self.on_game_state_update: Optional[Callable[[GameState], None]] = None
        self.on_game_over: Optional[Callable[[str, str], None]] = None
        self.on_error: Optional[Callable[[str, str], None]] = None
        self.on_player_joined: Optional[Callable[[Dict], None]] = None
        self.on_player_left: Optional[Callable[[str], None]] = None
        self.on_chat_message: Optional[Callable[[str, str], None]] = None
        self.on_undo_request: Optional[Callable[[str], None]] = None
        self.on_undo_response: Optional[Callable[[bool], None]] = None

        self._receive_task: Optional[asyncio.Task] = None
        self._state_event = asyncio.Event()
        self._state_event.set()

        self.local_session: Optional[GameSession] = None

    def _is_connected(self) -> bool:
        if self.ws is None: return False
        return self.ws.state == State.OPEN

    def get_display_state(self) -> Optional[GameDisplayState]:
        if not self.game_state:
            return None
        return GameDisplayState(
            board_size=self.board_size,
            board_array=self.game_state.board_array,
            current_player=self.game_state.current_player,
            move_number=self.game_state.move_number,
            passes=self.game_state.passes,
            last_move=self.game_state.last_move,
            captures=self.game_state.captures,
            player_color=self.player_color,
            is_my_turn=self.is_my_turn(),
            mode="network"
        )
    async def connect(self) -> bool:
        try:
            self.state = ConnectionState.CONNECTING
            self.ws = await websockets.connect(self.server_url)
            self.state = ConnectionState.CONNECTED
            await self._send(Message.connect(self.player_name))

            await asyncio.sleep(0.1)
            await self._send(Message.lobby_ready())


            # Запускаем обработчик входящих сообщений
            self._receive_task = asyncio.create_task(self._receive_loop())
            if self.on_connected: self.on_connected()
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.DISCONNECTED
            return False

    async def disconnect(self):
        if self.ws:
            try: await self.ws.close()
            except Exception: pass
        if self._receive_task:
            self._receive_task.cancel()
            try: await self._receive_task
            except asyncio.CancelledError: pass
        self.state = ConnectionState.DISCONNECTED
        if self.on_disconnected: self.on_disconnected()

    async def create_room(self, name: str, board_size: int = 19, password: Optional[str] = None, komi: float = 6.5, rules: str = "japanese") -> bool:
        if self.state != ConnectionState.CONNECTED: return False
        await self._send(Message.room_create(name=name, board_size=board_size, password=password, komi=komi, rules=rules))
        return True

    async def join_room(self, room_id: str, password: Optional[str] = None) -> bool:
        if self.state != ConnectionState.CONNECTED: return False
        await self._send(Message.room_join(room_id, password))
        return True

    async def leave_room(self):
        if self.room_id:
            await self._send(Message(MessageType.ROOM_LEAVE))
            self.room_id = None
            self.state = ConnectionState.CONNECTED

    async def set_ready(self, is_ready: bool = True):
        await self._send(Message.room_ready(is_ready))

    async def send_move(self, x: int, y: int) -> bool:
        if self.state != ConnectionState.PLAYING or not self.game_state: return False
        if self.game_state.current_player != self.player_color: return False
        await self._send(Message.game_move(x, y, self.game_state.move_number))
        return True

    async def send_pass(self) -> bool:
        if self.state != ConnectionState.PLAYING or not self.game_state: return False
        await self._send(Message.game_pass(self.game_state.move_number))
        return True

    async def send_resign(self):
        await self._send(Message(MessageType.GAME_RESIGN))

    async def request_undo(self):
        if not self.game_state: return
        await self._send(Message.undo_request(self.game_state.move_number))

    async def send_chat(self, text: str):
        await self._send(Message.game_chat(self.player_name, text))

    async def _send(self, message: Message):
        if self._is_connected():
            try: await self.ws.send(message.to_json())
            except Exception as e: logger.error(f"Send error: {e}")
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
            self.state = ConnectionState.DISCONNECTED

    async def _handle_message(self, data: str):
        try:
            msg = Message.from_json(data)
            handler = getattr(self, f"_on_{msg.type.value}", None)
            if handler: await handler(msg)
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def _on_error(self, msg: Message):
        code = msg.payload.get("code", "UNKNOWN")
        message = msg.payload.get("message", "Unknown error")
        if self.on_error: self.on_error(code, message)

    async def _on_room_list(self, msg: Message):
        rooms_data = msg.payload.get("rooms", [])
        rooms = [RoomInfo(**r) for r in rooms_data]
        if self.on_room_list: self.on_room_list(rooms)

    async def _on_room_join(self, msg: Message):
        if msg.payload.get("success"):
            self.room_id = msg.payload.get("room_id")
            self.player_color = msg.payload.get("player_color")
            self.state = ConnectionState.IN_ROOM
            if self.on_room_joined: self.on_room_joined(self.room_id, self.player_color)
        else:
            if self.on_error: self.on_error("JOIN_FAILED", msg.payload.get("message", "Unknown"))

    async def _on_room_update(self, msg: Message):
        if self.on_room_update: self.on_room_update(msg.payload)
        event = msg.payload.get("event", "")
        if event == "player_joined" and self.on_player_joined:
            self.on_player_joined(msg.payload.get("players", []))
        elif event == "player_left" and self.on_player_left:
            self.on_player_left("unknown")

    async def _on_game_start(self, msg: Message):
        self.state = ConnectionState.PLAYING
        self.board_size = msg.payload.get("board_size", 19)
        initial = msg.payload.get("initial_state", {})
        self.game_state = GameState(
            board_array=initial.get("board", []),
            current_player=initial.get("current_player", "black"),
            move_number=initial.get("move_number", 1),
            passes=initial.get("passes", 0),
            captures=initial.get("captures", {"black": 0, "white": 0})
        )
        self._state_event.set()          # <-- будим цикл
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
        self._state_event.set()          # <-- будим ожидающий цикл
        if self.on_game_state_update:
            self.on_game_state_update(self.game_state)


    async def _on_game_move(self, msg: Message):
        if self.on_move_received: self.on_move_received(msg.payload.get("move", {}))

    async def _on_game_pass(self, msg: Message):
        await self._on_game_state(Message(MessageType.GAME_STATE, msg.payload.get("board_state", {})))
        if self.on_move_received: self.on_move_received(msg.payload.get("move", {}))

    async def _on_game_over(self, msg: Message):
        self.state = ConnectionState.IN_ROOM
        self._state_event.set()          # <-- будим цикл, чтобы не ждать 60 сек
        winner = msg.payload.get("winner", "")
        result = msg.payload.get("result", "")
        if self.on_game_over:
            self.on_game_over(winner, result)

    async def _on_game_chat(self, msg: Message):
        if self.on_chat_message:
            self.on_chat_message(msg.payload.get("sender", ""), msg.payload.get("text", ""))

    async def _on_game_undo_request(self, msg: Message):
        if self.on_undo_request: self.on_undo_request(msg.payload.get("requester", ""))

    async def _on_game_undo_response(self, msg: Message):
        if self.on_undo_response: self.on_undo_response(msg.payload.get("accepted", False))

    def is_my_turn(self) -> bool:
        if not self.game_state or not self.player_color: return False
        return self.game_state.current_player == self.player_color

    def get_local_board(self) -> Optional[go.Board]:
        if not self.game_state: return None
        board = go.Board(self.board_size)
        array = self.game_state.board_array
        for y in range(self.board_size):
            for x in range(self.board_size):
                val = array[y][x] if y < len(array) and x < len(array[y]) else 0
                if val == 1: board.add_stone(x, y, go.Color.Black)
                elif val == 2: board.add_stone(x, y, go.Color.White)
        return board

    def format_move(self, x: int, y: int) -> str:
        from core_adapter import CoordinateUtils
        return CoordinateUtils.format_move(x, y)
    
    