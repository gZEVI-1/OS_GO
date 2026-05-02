"""
OS-GO Network Server
====================

WebSocket сервер для сетевой игры в Го.
Управляет лобби, комнатами и игровыми сессиями.

Запуск:
    python server.py [--host 0.0.0.0] [--port 8765]
    ip сервера 192.168.1.1
Архитектура:
    - GameServer: главный сервер, управляет подключениями
    - Lobby: управление комнатами
    - GameRoom: игровая комната с логикой go_engine
    - PlayerConnection: обертка над WebSocket соединением

Зависимости:
    websockets>=16.0, go_engine (через core_adapter)
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field
from datetime import datetime
import argparse

import websockets
from websockets.server import WebSocketServerProtocol
from websockets.protocol import State  # websockets 16.0+

# Импорт протокола
from protocol import Message, MessageType, RoomInfo, PlayerInfo, GameAction


import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core_adapter import GameSession, PlayerType
import go_engine as go


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("GoServer")


# ============================================================================
# ИСКЛЮЧЕНИЯ
# ============================================================================

class ProtocolError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


# ============================================================================
# ИГРОВАЯ КОМНАТА
# ============================================================================

@dataclass
class RoomPlayer:
    """Игрок в комнате"""
    player_id: str
    name: str
    websocket: WebSocketServerProtocol
    color: Optional[str] = None
    is_ready: bool = False
    is_connected: bool = True

    def to_info(self) -> PlayerInfo:
        return PlayerInfo(
            player_id=self.player_id,
            name=self.name,
            color=self.color,
            is_ready=self.is_ready,
            is_connected=self.is_connected
        )


class GameRoom:
    """
    Игровая комната с полной логикой go_engine.

    Жизненный цикл:
        waiting -> playing -> finished
    """

    def __init__(self, room_id: str, name: str, host_id: str,
                 board_size: int = 19, password: Optional[str] = None,
                 komi: float = 6.5, rules: str = "japanese"):
        self.room_id = room_id
        self.name = name
        self.host_id = host_id
        self.board_size = board_size
        self.password = password
        self.komi = komi
        self.rules = rules

        self.players: Dict[str, RoomPlayer] = {}  # player_id -> RoomPlayer
        self.spectators: Dict[str, RoomPlayer] = {}  # Зрители

        self.status = "waiting"  # waiting, playing, finished
        self.game: Optional[go.Game] = None
        self.game_session: Optional[GameSession] = None

        self.move_history: List[dict] = []
        self.captures = {"black": 0, "white": 0}
        self.chat_history: List[dict] = []

        self.created_at = datetime.now()
        self.game_started_at: Optional[datetime] = None

        # Для отмены хода
        self.pending_undo: Optional[str] = None  # player_id запросивший отмену

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def max_players(self) -> int:
        return 2

    @property
    def has_password(self) -> bool:
        return self.password is not None

    def to_info(self) -> RoomInfo:
        return RoomInfo(
            room_id=self.room_id,
            name=self.name,
            host_name=self.get_host_name(),
            board_size=self.board_size,
            has_password=self.has_password,
            player_count=self.player_count,
            max_players=self.max_players,
            status=self.status
        )

    def get_host_name(self) -> str:
        if self.host_id in self.players:
            return self.players[self.host_id].name
        return "Unknown"

    def add_player(self, player: RoomPlayer) -> bool:
        """Добавляет игрока в комнату. Возвращает True если успешно."""
        if self.player_count >= self.max_players:
            return False

        # Назначаем цвет
        if self.player_count == 0:
            player.color = "black"
        else:
            player.color = "white"

        self.players[player.player_id] = player
        return True

    def remove_player(self, player_id: str):
        """Удаляет игрока из комнаты"""
        if player_id in self.players:
            del self.players[player_id]
            # Если ушел host, назначаем нового
            if player_id == self.host_id and self.players:
                self.host_id = next(iter(self.players.keys()))

    def get_player_by_ws(self, ws: WebSocketServerProtocol) -> Optional[RoomPlayer]:
        for p in self.players.values():
            if p.websocket == ws:
                return p
        for p in self.spectators.values():
            if p.websocket == ws:
                return p
        return None

    def set_ready(self, player_id: str, is_ready: bool):
        if player_id in self.players:
            self.players[player_id].is_ready = is_ready

    def all_ready(self) -> bool:
        return (len(self.players) == self.max_players and
                all(p.is_ready for p in self.players.values()))

    def start_game(self) -> bool:
        """Инициализирует игру через go_engine"""
        if not self.all_ready():
            return False

        self.status = "playing"
        self.game = go.Game(size=self.board_size)
        self.game_started_at = datetime.now()
        self.move_history = []

        # Инициализируем GameSession для совместимости
        # (хотя для сервера используем go.Game напрямую)

        logger.info(f"Game started in room {self.room_id}, size={self.board_size}")
        return True

    def make_move(self, player_id: str, x: int, y: int) -> dict:
        """
        Выполняет ход. Возвращает результат с флагом success.
        """
        if self.status != "playing" or not self.game:
            return {"success": False, "error": "Игра не начата"}

        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}

        # Проверяем очередь хода
        current = self.game.get_current_player()
        expected_color = GameAction.str_to_color(player.color)
        if current != expected_color:
            return {"success": False, "error": "Сейчас не ваш ход"}

        # Выполняем ход через go_engine
        success = self.game.make_move(x, y)
        if not success:
            return {"success": False, "error": "Нелегальный ход"}

        # Сохраняем в историю
        move_record = {
            "x": x, "y": y,
            "color": player.color,
            "move_number": self.game.get_move_number() - 1,
            "player_name": player.name,
            "timestamp": datetime.now().isoformat()
        }
        self.move_history.append(move_record)

        # Проверяем конец игры
        is_over = self.game.is_game_over()

        return {
            "success": True,
            "move": move_record,
            "game_over": is_over,
            "board_state": self.get_game_state()
        }

    def make_pass(self, player_id: str) -> dict:
        """Пас игрока"""
        if self.status != "playing" or not self.game:
            return {"success": False, "error": "Игра не начата"}

        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}

        current = self.game.get_current_player()
        expected_color = GameAction.str_to_color(player.color)
        if current != expected_color:
            return {"success": False, "error": "Сейчас не ваш ход"}

        success = self.game.make_move(-1, -1, is_pass=True)

        move_record = {
            "x": -1, "y": -1,
            "color": player.color,
            "move_number": self.game.get_move_number() - 1,
            "is_pass": True,
            "player_name": player.name,
            "timestamp": datetime.now().isoformat()
        }
        self.move_history.append(move_record)

        is_over = self.game.is_game_over()

        return {
            "success": True,
            "move": move_record,
            "game_over": is_over,
            "board_state": self.get_game_state()
        }

    def request_undo(self, player_id: str) -> dict:
        """Запрос отмены хода"""
        if len(self.move_history) == 0:
            return {"success": False, "error": "Нет ходов для отмены"}

        self.pending_undo = player_id
        requester = self.players[player_id]

        # Определяем оппонента
        opponent_id = next(
            (pid for pid, p in self.players.items() if pid != player_id),
            None
        )

        return {
            "success": True,
            "requester": requester.name,
            "opponent_id": opponent_id
        }

    def confirm_undo(self, accepted: bool) -> dict:
        """Подтверждение/отклонение отмены"""
        if not self.pending_undo:
            return {"success": False, "error": "Нет активного запроса на отмену"}

        if not accepted:
            self.pending_undo = None
            return {"success": True, "accepted": False}

        # Отменяем последний ход
        if self.game and len(self.move_history) > 0:
            self.game.undo_last_move()
            self.move_history.pop()

        self.pending_undo = None

        return {
            "success": True,
            "accepted": True,
            "board_state": self.get_game_state()
        }

    def get_game_state(self) -> dict:
        """Возвращает текущее состояние игры для синхронизации"""
        if not self.game:
            return {}

        board = self.game.get_board_const()
        last_move = self.move_history[-1] if self.move_history else None

        return {
            "board": GameAction.board_to_array(board),
            "current_player": GameAction.color_to_str(self.game.get_current_player()),
            "move_number": self.game.get_move_number(),
            "passes": self.game.get_passes(),
            "last_move": last_move,
            "captures": self.captures
        }

    def resign(self, player_id: str) -> dict:
        """Игрок сдается"""
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}

        winner = "white" if player.color == "black" else "black"
        self.status = "finished"

        return {
            "success": True,
            "winner": winner,
            "reason": "resign",
            "resigned_player": player.name
        }

    def broadcast(self, message: Message, exclude: Optional[str] = None):
        """Отправляет сообщение всем игрокам в комнате"""
        tasks = []
        for pid, player in self.players.items():
            if pid != exclude and player.is_connected:
                tasks.append(self._send(player.websocket, message))

        if tasks:
            asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))

    async def _send(self, ws: WebSocketServerProtocol, message: Message):
        try:
            await ws.send(message.to_json())
        except Exception as e:
            logger.warning(f"Failed to send message: {e}")

    def get_players_info(self) -> List[PlayerInfo]:
        return [p.to_info() for p in self.players.values()]


# ============================================================================
# ЛОББИ
# ============================================================================

class Lobby:
    """Управление всеми игровыми комнатами"""

    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.player_rooms: Dict[str, str] = {}  # player_id -> room_id

    def create_room(self, name: str, host_id: str, host_ws: WebSocketServerProtocol,
                    host_name: str, **kwargs) -> GameRoom:
        room_id = str(uuid.uuid4())[:8]
        room = GameRoom(room_id=room_id, name=name, host_id=host_id, **kwargs)

        host_player = RoomPlayer(
            player_id=host_id,
            name=host_name,
            websocket=host_ws,
            color="black"
        )
        room.add_player(host_player)

        self.rooms[room_id] = room
        self.player_rooms[host_id] = room_id

        return room

    def join_room(self, room_id: str, player_id: str,
                  player_ws: WebSocketServerProtocol,
                  player_name: str, password: Optional[str] = None) -> Optional[GameRoom]:
        room = self.rooms.get(room_id)
        if not room:
            return None

        if room.password and room.password != password:
            raise ProtocolError("WRONG_PASSWORD", "Неверный пароль комнаты")

        if room.player_count >= room.max_players:
            raise ProtocolError("ROOM_FULL", "Комната заполнена")

        if room.status != "waiting":
            raise ProtocolError("GAME_STARTED", "Игра уже начата")

        player = RoomPlayer(
            player_id=player_id,
            name=player_name,
            websocket=player_ws
        )

        if room.add_player(player):
            self.player_rooms[player_id] = room_id
            return room
        return None

    def leave_room(self, player_id: str) -> Optional[GameRoom]:
        room_id = self.player_rooms.get(player_id)
        if not room_id:
            return None

        room = self.rooms.get(room_id)
        if room:
            room.remove_player(player_id)

            # Удаляем пустую комнату
            if room.player_count == 0:
                del self.rooms[room_id]

            del self.player_rooms[player_id]
            return room
        return None

    def get_room_list(self) -> List[RoomInfo]:
        return [r.to_info() for r in self.rooms.values()]

    def get_player_room(self, player_id: str) -> Optional[GameRoom]:
        room_id = self.player_rooms.get(player_id)
        return self.rooms.get(room_id) if room_id else None


# ============================================================================
# СЕРВЕР
# ============================================================================

class GameServer:
    """
    Главный WebSocket сервер.

    Использование:
        server = GameServer(host="0.0.0.0", port=8765)
        asyncio.run(server.start())
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.lobby = Lobby()
        self.connections: Dict[WebSocketServerProtocol, dict] = {}
        self.players: Dict[str, dict] = {}  # player_id -> {name, ws, room}

    async def start(self):
        logger.info(f"Starting server on ws://{self.host}:{self.port}")
        # websockets 16.0+: handler принимает только connection
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()  # run forever

    # ИСПРАВЛЕНО: убран аргумент path для websockets 16.0+
    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """Обработка нового подключения"""
        player_id = str(uuid.uuid4())[:8]

        self.connections[websocket] = {
            "player_id": player_id,
            "name": None,
            "authenticated": False
        }

        logger.info(f"New connection: {player_id} from {websocket.remote_address}")

        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {player_id}")
        finally:
            await self.disconnect(websocket)

    async def handle_message(self, websocket: WebSocketServerProtocol, data: str):
        """Маршрутизация сообщений"""
        try:
            msg = Message.from_json(data)
            handler = getattr(self, f"handle_{msg.type.value}", None)

            if handler:
                await handler(websocket, msg)
            else:
                await self.send_error(websocket, "UNKNOWN_TYPE", f"Unknown message type: {msg.type.value}")

        except json.JSONDecodeError:
            await self.send_error(websocket, "INVALID_JSON", "Invalid JSON format")
        except Exception as e:
            logger.exception("Error handling message")
            await self.send_error(websocket, "INTERNAL_ERROR", str(e))

    # --- Обработчики сообщений ---

    async def handle_connect(self, ws: WebSocketServerProtocol, msg: Message):
        """Первичное подключение игрока"""
        name = msg.payload.get("player_name", f"Player_{uuid.uuid4().hex[:4]}")
        version = msg.payload.get("version", "unknown")

        self.connections[ws]["name"] = name
        self.connections[ws]["authenticated"] = True

        logger.info(f"Player connected: {name} (protocol v{version})")

        # Игнорируем запросы списка комнат - клиент получит их через lobby_ready
        # Список комнат будет отправлен после подтверждения готовности лобби

    async def handle_lobby_ready(self, ws: WebSocketServerProtocol, msg: Message):
        """Обработка сигнала готовности лобби - отправляем список комнат"""
        conn = self.connections.get(ws)
        if not conn or not conn["authenticated"]:
            return

        # Отправляем список комнат только после подтверждения готовности клиента
        rooms = self.lobby.get_room_list()
        await ws.send(Message.room_list(rooms).to_json())
        logger.debug(f"Sent room list to {conn['name']}")

    async def handle_room_create(self, ws: WebSocketServerProtocol, msg: Message):
        """Создание комнаты"""
        conn = self.connections[ws]
        if not conn["authenticated"]:
            await self.send_error(ws, "NOT_AUTHENTICATED", "Сначала отправьте connect")
            return

        player_id = conn["player_id"]
        name = msg.payload.get("name", f"Room_{player_id}")
        board_size = msg.payload.get("board_size", 19)
        password = msg.payload.get("password")
        komi = msg.payload.get("komi", 6.5)
        rules = msg.payload.get("rules", "japanese")

        room = self.lobby.create_room(
            name=name,
            host_id=player_id,
            host_ws=ws,
            host_name=conn["name"],
            board_size=board_size,
            password=password,
            komi=komi,
            rules=rules
        )

        self.players[player_id] = {
            "name": conn["name"],
            "ws": ws,
            "room_id": room.room_id
        }

        # Отправляем подтверждение
        await ws.send(Message(MessageType.ROOM_JOIN, {
            "success": True,
            "room_id": room.room_id,
            "player_color": "black",
            "players": [p.to_dict() for p in room.get_players_info()]
        }).to_json())

        logger.info(f"Room created: {room.room_id} by {conn['name']}")

    async def handle_room_join(self, ws: WebSocketServerProtocol, msg: Message):
        """Вход в комнату"""
        conn = self.connections[ws]
        if not conn["authenticated"]:
            await self.send_error(ws, "NOT_AUTHENTICATED", "Сначала отправьте connect")
            return

        player_id = conn["player_id"]
        room_id = msg.payload.get("room_id")
        password = msg.payload.get("password")

        try:
            room = self.lobby.join_room(
                room_id=room_id,
                player_id=player_id,
                player_ws=ws,
                player_name=conn["name"],
                password=password
            )

            if not room:
                await self.send_error(ws, "JOIN_FAILED", "Не удалось войти в комнату")
                return

            self.players[player_id] = {
                "name": conn["name"],
                "ws": ws,
                "room_id": room_id
            }

            # Уведомляем нового игрока
            player = room.players.get(player_id)
            await ws.send(Message(MessageType.ROOM_JOIN, {
                "success": True,
                "room_id": room_id,
                "player_color": player.color,
                "players": [p.to_dict() for p in room.get_players_info()]
            }).to_json())

            # Уведомляем остальных
            room.broadcast(Message(MessageType.ROOM_UPDATE, {
                "event": "player_joined",
                "players": [p.to_dict() for p in room.get_players_info()]
            }), exclude=player_id)

            logger.info(f"Player {conn['name']} joined room {room_id}")

        except ProtocolError as e:
            await self.send_error(ws, e.code, e.message)

    async def handle_room_ready(self, ws: WebSocketServerProtocol, msg: Message):
        """Игрок готов к игре"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if not room:
            await self.send_error(ws, "NOT_IN_ROOM", "Вы не в комнате")
            return

        is_ready = msg.payload.get("is_ready", True)
        room.set_ready(player_id, is_ready)

        # Обновляем всех
        room.broadcast(Message(MessageType.ROOM_UPDATE, {
            "event": "player_ready",
            "players": [p.to_dict() for p in room.get_players_info()]
        }))

        # Если все готовы — начинаем игру
        if room.all_ready():
            room.start_game()
            state = room.get_game_state()

            room.broadcast(Message(MessageType.GAME_START, {
                "board_size": room.board_size,
                "komi": room.komi,
                "rules": room.rules,
                "players": [p.to_dict() for p in room.get_players_info()],
                "initial_state": state
            }))

            logger.info(f"Game started in room {room.room_id}")

    async def handle_game_move(self, ws: WebSocketServerProtocol, msg: Message):
        """Обработка хода"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if not room or room.status != "playing":
            await self.send_error(ws, "NOT_PLAYING", "Игра не активна")
            return

        x = msg.payload.get("x")
        y = msg.payload.get("y")

        result = room.make_move(player_id, x, y)

        if not result["success"]:
            await self.send_error(ws, "INVALID_MOVE", result["error"])
            return

        # Рассылаем всем обновленное состояние
        room.broadcast(Message.game_state(**result["board_state"]))

        # Если игра окончена
        if result.get("game_over"):
            winner = result["board_state"]["current_player"]  # Последний ходивший
            room.status = "finished"
            room.broadcast(Message.game_over(
                winner=winner,
                result="Игра окончена (два паса)",
                reason="two_passes"
            ))

    async def handle_game_pass(self, ws: WebSocketServerProtocol, msg: Message):
        """Обработка паса"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if not room or room.status != "playing":
            await self.send_error(ws, "NOT_PLAYING", "Игра не активна")
            return

        result = room.make_pass(player_id)

        if not result["success"]:
            await self.send_error(ws, "INVALID_PASS", result["error"])
            return

        room.broadcast(Message(MessageType.GAME_PASS, {
            "move": result["move"],
            "board_state": result["board_state"]
        }))

        if result.get("game_over"):
            winner = "black" if result["move"]["color"] == "white" else "white"
            room.status = "finished"
            room.broadcast(Message.game_over(
                winner=winner,
                result="Игра окончена (два паса)",
                reason="two_passes"
            ))

    async def handle_game_resign(self, ws: WebSocketServerProtocol, msg: Message):
        """Сдача"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if not room or room.status != "playing":
            return

        result = room.resign(player_id)
        room.broadcast(Message.game_over(
            winner=result["winner"],
            result=f"{result['resigned_player']} сдался",
            reason="resign"
        ))

    async def handle_game_undo_request(self, ws: WebSocketServerProtocol, msg: Message):
        """Запрос отмены хода"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if not room or room.status != "playing":
            return

        result = room.request_undo(player_id)
        if result["success"]:
            # Отправляем оппоненту запрос
            opponent_ws = room.players.get(result["opponent_id"])
            if opponent_ws:
                await opponent_ws.websocket.send(Message(MessageType.GAME_UNDO_REQUEST, {
                    "requester": result["requester"],
                    "move_number": msg.payload.get("move_number")
                }).to_json())

    async def handle_game_undo_response(self, ws: WebSocketServerProtocol, msg: Message):
        """Ответ на запрос отмены"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if not room:
            return

        accepted = msg.payload.get("accepted", False)
        result = room.confirm_undo(accepted)

        if result["success"] and result.get("accepted"):
            room.broadcast(Message(MessageType.GAME_STATE, result["board_state"]))
        else:
            # Уведомляем запросившего об отказе
            if room.pending_undo:
                requester = room.players.get(room.pending_undo)
                if requester:
                    await requester.websocket.send(Message(MessageType.GAME_UNDO_RESPONSE, {
                        "accepted": False
                    }).to_json())

    async def handle_room_leave(self, ws: WebSocketServerProtocol, msg: Message):
        """Выход из комнаты"""
        conn = self.connections[ws]
        player_id = conn["player_id"]

        room = self.lobby.leave_room(player_id)
        if room:
            room.broadcast(Message(MessageType.ROOM_UPDATE, {
                "event": "player_left",
                "players": [p.to_dict() for p in room.get_players_info()]
            }))

    async def handle_game_chat(self, ws: WebSocketServerProtocol, msg: Message):
        """Чат в игре"""
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)

        if room:
            text = msg.payload.get("text", "")
            room.chat_history.append({
                "sender": conn["name"],
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
            room.broadcast(Message.game_chat(conn["name"], text))

    async def disconnect(self, websocket: WebSocketServerProtocol):
        """Обработка отключения"""
        conn = self.connections.get(websocket)
        if not conn:
            return

        player_id = conn["player_id"]

        # Удаляем из комнаты
        room = self.lobby.leave_room(player_id)
        if room:
            room.broadcast(Message(MessageType.ROOM_UPDATE, {
                "event": "player_disconnected",
                "players": [p.to_dict() for p in room.get_players_info()]
            }))

        # Очистка
        if player_id in self.players:
            del self.players[player_id]
        del self.connections[websocket]

    async def send_error(self, ws: WebSocketServerProtocol, code: str, message: str):
        await ws.send(Message.error(code, message).to_json())


# ============================================================================
# ТОЧКА ВХОДА
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="OS-GO Network Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind (default: 8765)")
    args = parser.parse_args()

    server = GameServer(host=args.host, port=args.port)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()