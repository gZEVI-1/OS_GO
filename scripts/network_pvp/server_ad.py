
"""
OS-GO Network Server — PySide6-Ready Edition
=============================================
WebSocket сервер для сетевой игры в Го.

Изменения для стабильности GUI-клиентов:
- Унифицирована логика завершения игры (DRY)
- Исправлена логика undo (opponent_id, pending_undo)
- Добавлена обработка внезапного отключения во время игры
- calculate_score теперь кроссплатформенный (ищет gnugo в PATH)
- Улучшена надёжность broadcast (изоляция ошибок по клиентам)

Запуск:
    python server.py --host 0.0.0.0 --port 8765
"""

import asyncio
import json
import uuid
import logging
import os
import sys
import shutil
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field
from datetime import datetime
import argparse

import websockets
from websockets import WebSocketServerProtocol
from websockets.protocol import State

from protocol import Message, MessageType, RoomInfo, PlayerInfo, GameAction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import go_engine as go
from core_adapter import GameSession, PlayerType

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
    """Игрок в комнате."""
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
    Жизненный цикл: waiting -> playing -> finished
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

        self.players: Dict[str, RoomPlayer] = {}
        self.spectators: Dict[str, RoomPlayer] = {}

        self.status = "waiting"  # waiting, playing, finished
        self.session: Optional[GameSession] = None

        self.move_history: List[dict] = []
        self.captures = {"black": 0, "white": 0}
        self.chat_history: List[dict] = []

        self.created_at = datetime.now()
        self.game_started_at: Optional[datetime] = None

        # Для отмены хода
        self.pending_undo: Optional[str] = None  # player_id запросивший отмену
        self.pending_undo_target: Optional[str] = None  # player_id кому отправлять ответ

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
        if self.player_count >= self.max_players:
            return False
        if self.player_count == 0:
            player.color = "black"
        else:
            player.color = "white"
        self.players[player.player_id] = player
        return True

    def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
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

    def get_opponent_id(self, player_id: str) -> Optional[str]:
        """Возвращает ID оппонента (для 2 игроков)."""
        for pid in self.players:
            if pid != player_id:
                return pid
        return None

    def set_ready(self, player_id: str, is_ready: bool):
        if player_id in self.players:
            self.players[player_id].is_ready = is_ready

    def all_ready(self) -> bool:
        return (len(self.players) == self.max_players and
                all(p.is_ready for p in self.players.values()))

    def start_game(self) -> bool:
        if not self.all_ready():
            return False
        self.session = GameSession(self.board_size, self.komi)
        for pid, player in self.players.items():
            color = GameAction.str_to_color(player.color)
            self.session.set_player(color, player.name, PlayerType.NETWORK)
        self.session.game_active = True
        self.status = "playing"
        self.game_started_at = datetime.now()
        self.move_history = []

        self.session.add_move_callback(self._on_move)
        self.session.add_pass_callback(self._on_pass)
        self.session.add_game_over_callback(self._on_game_over)

        logger.info(f"Game started in room {self.room_id}")
        return True

    def make_move(self, player_id: str, x: int, y: int) -> dict:
        if self.status != "playing" or not self.session:
            return {"success": False, "error": "Игра не начата"}
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        color = GameAction.str_to_color(player.color)
        result = self.session.make_move(x, y, False, color)
        if not result.success:
            return {"success": False, "error": result.message}
        return {
            "success": True,
            "move": result.move_info,
            "game_over": result.game_over,
            "board_state": self.session.get_state_dict()
        }

    def make_pass(self, player_id: str) -> dict:
        player = self.players.get(player_id)
        if not player or not self.session:
            return {"success": False, "error": "Игрок не найден"}
        color = GameAction.str_to_color(player.color)
        result = self.session.make_pass(color)
        if not result.success:
            return {"success": False, "error": result.message}
        return {
            "success": True,
            "move": result.move_info,
            "game_over": result.game_over,
            "board_state": self.session.get_state_dict()
        }

    def request_undo(self, player_id: str) -> dict:
        if not self.session or len(self.move_history) == 0:
            return {"success": False, "error": "Нет ходов для отмены"}
        opponent_id = self.get_opponent_id(player_id)
        if not opponent_id:
            return {"success": False, "error": "Нет оппонента"}
        # Отмена через session.undo_move()
        success = self.session.undo_move()
        if success:
            self.move_history.pop()
        return {
            "success": success,
            "opponent_id": opponent_id,
            "requester": self.players.get(player_id, RoomPlayer("", "", None)).name,
            "board_state": self.session.get_state_dict() if success else None
        }

    def confirm_undo(self, accepted: bool) -> dict:
        if not self.pending_undo:
            return {"success": False, "error": "Нет активного запроса на отмену"}
        if not accepted:
            self.pending_undo = None
            self.pending_undo_target = None
            return {"success": True, "accepted": False}
        if self.session and len(self.move_history) > 0:
            self.session.undo_move()
            self.move_history.pop()
        self.pending_undo = None
        self.pending_undo_target = None
        return {
            "success": True,
            "accepted": True,
            "board_state": self.get_game_state()
        }

    def get_game_state(self) -> dict:
        if not self.session:
            return {}
        state = self.session.get_state_dict()
        if self.move_history:
            last = self.move_history[-1]
            state["last_move"] = {
                "x": last.get("x", -1),
                "y": last.get("y", -1),
                "color": last.get("color", ""),
                "is_pass": last.get("is_pass", False),
                "move_number": last.get("move_number", 0)
            }
        else:
            state["last_move"] = None
        return state

    def calculate_score(self) -> Optional[Dict]:
        """Пытается подсчитать очки через GNU Go Analyzer. Кроссплатформенный поиск."""
        if not self.session:
            return None
        try:
            # Ищем gnugo в PATH и в стандартных локациях
            gnugo_path = None
            if sys.platform == "win32":
                candidates = ["gnugo.exe", "gnugo-3.8\\gnugo.exe", "bot\\gnugo-3.8\\gnugo.exe"]
            else:
                candidates = ["gnugo", "gnugo-3.8/gnugo", "bot/gnugo-3.8/gnugo"]
            
            # Поиск в PATH
            for cand in candidates:
                path = shutil.which(cand)
                if path:
                    gnugo_path = path
                    break
            
            # Поиск относительно скрипта
            if not gnugo_path:
                base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                for cand in candidates:
                    p = os.path.join(base, cand)
                    if os.path.exists(p):
                        gnugo_path = p
                        break
            
            if not gnugo_path or not os.path.exists(gnugo_path):
                return None

            if base not in sys.path:
                sys.path.insert(0, base)
            import GnuGo_Analyzer

            analyzer = None
            for name in dir(GnuGo_Analyzer):
                if name.startswith('_'):
                    continue
                obj = getattr(GnuGo_Analyzer, name)
                if isinstance(obj, type) and hasattr(obj, 'analyze_sgf'):
                    analyzer = obj(gnugo_path)
                    break
                elif callable(obj) and hasattr(obj, 'analyze_sgf'):
                    analyzer = obj
                    break

            if not analyzer or not hasattr(self.session.game, 'get_sgf'):
                return None

            sgf = self.session.game.get_sgf()
            result = analyzer.analyze_sgf(sgf, self.board_size)
            return result

        except Exception:
            logger.exception("calculate_score error")
            return None

    def resign(self, player_id: str) -> dict:
        player = self.players.get(player_id)
        if not player:
            return {"success": False, "error": "Игрок не найден"}
        color = GameAction.str_to_color(player.color)
        if self.session:
            self.session.resign(color)
        self.status = "finished"
        return {
            "success": True,
            "winner": "white" if player.color == "black" else "black",
            "reason": "resign",
            "resigned_player": player.name
        }

    def handle_player_disconnect(self, player_id: str) -> Optional[dict]:
        """Обрабатывает отключение игрока. Возвращает результат game_over если игра активна."""
        if player_id in self.players:
            self.players[player_id].is_connected = False
        if self.status == "playing":
            # Игрок отключился во время игры — оппонент побеждает
            opponent_id = self.get_opponent_id(player_id)
            if opponent_id and opponent_id in self.players:
                opponent = self.players[opponent_id]
                self.status = "finished"
                return {
                    "winner": opponent.color,
                    "result": f"{opponent.name} победил (отключение оппонента)",
                    "reason": "disconnect"
                }
        return None

    async def broadcast(self, message: Message, exclude: Optional[str] = None):
        """Отправляет сообщение всем игрокам. Ошибки изолируются по клиентам."""
        tasks = []
        for pid, player in self.players.items():
            if pid != exclude and player.is_connected:
                tasks.append(self._send_safe(player.websocket, message))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    logger.warning(f"Broadcast send error: {res}")

    async def _send_safe(self, ws: WebSocketServerProtocol, message: Message):
        """Безопасная отправка с обработкой исключения."""
        try:
            await ws.send(message.to_json())
        except Exception as e:
            logger.warning(f"Failed to send message: {e}")

    def get_players_info(self) -> List[PlayerInfo]:
        return [p.to_info() for p in self.players.values()]

    def _on_move(self, move_info: Dict):
        self.move_history.append(move_info)

    def _on_pass(self, move_info: Dict):
        self.move_history.append(move_info)

    def _on_game_over(self):
        self.status = "finished"


# ============================================================================
# ЛОББИ
# ============================================================================

class Lobby:
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.player_rooms: Dict[str, str] = {}

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
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.lobby = Lobby()
        self.connections: Dict[WebSocketServerProtocol, dict] = {}
        self.players: Dict[str, dict] = {}

    async def start(self):
        logger.info(f"Starting server on ws://{self.host}:{self.port}")
        async with websockets.serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()

    async def handle_connection(self, websocket: WebSocketServerProtocol):
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
        try:
            msg = Message.from_json(data)
            handler = getattr(self, f"handle_{msg.type.value}", None)
            if handler:
                await handler(websocket, msg)
            else:
                await self.send_error(websocket, "UNKNOWN_TYPE", f"Unknown: {msg.type.value}")
        except json.JSONDecodeError:
            await self.send_error(websocket, "INVALID_JSON", "Invalid JSON")
        except Exception as e:
            logger.exception("Error handling message")
            await self.send_error(websocket, "INTERNAL_ERROR", str(e))

    # --- Обработчики ---

    async def handle_connect(self, ws: WebSocketServerProtocol, msg: Message):
        name = msg.payload.get("player_name", f"Player_{uuid.uuid4().hex[:4]}")
        version = msg.payload.get("version", "unknown")
        self.connections[ws]["name"] = name
        self.connections[ws]["authenticated"] = True
        logger.info(f"Player connected: {name} (v{version})")

    async def handle_lobby_ready(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections.get(ws)
        if not conn or not conn["authenticated"]:
            return
        rooms = self.lobby.get_room_list()
        await ws.send(Message.room_list(rooms).to_json())

    async def handle_room_create(self, ws: WebSocketServerProtocol, msg: Message):
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
            name=name, host_id=player_id, host_ws=ws,
            host_name=conn["name"], board_size=board_size,
            password=password, komi=komi, rules=rules
        )
        self.players[player_id] = {"name": conn["name"], "ws": ws, "room_id": room.room_id}

        await ws.send(Message(MessageType.ROOM_JOIN, {
            "success": True,
            "room_id": room.room_id,
            "player_color": "black",
            "players": [p.to_dict() for p in room.get_players_info()]
        }).to_json())
        logger.info(f"Room created: {room.room_id} by {conn['name']}")

    async def handle_room_join(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        if not conn["authenticated"]:
            await self.send_error(ws, "NOT_AUTHENTICATED", "Сначала отправьте connect")
            return
        player_id = conn["player_id"]
        room_id = msg.payload.get("room_id")
        password = msg.payload.get("password")
        try:
            room = self.lobby.join_room(
                room_id=room_id, player_id=player_id,
                player_ws=ws, player_name=conn["name"], password=password
            )
            if not room:
                await self.send_error(ws, "JOIN_FAILED", "Не удалось войти")
                return
            self.players[player_id] = {"name": conn["name"], "ws": ws, "room_id": room_id}
            player = room.players.get(player_id)
            await ws.send(Message(MessageType.ROOM_JOIN, {
                "success": True,
                "room_id": room_id,
                "player_color": player.color,
                "players": [p.to_dict() for p in room.get_players_info()]
            }).to_json())
            await room.broadcast(Message(MessageType.ROOM_UPDATE, {
                "event": "player_joined",
                "players": [p.to_dict() for p in room.get_players_info()]
            }), exclude=player_id)
            logger.info(f"Player {conn['name']} joined room {room_id}")
        except ProtocolError as e:
            await self.send_error(ws, e.code, e.message)

    async def handle_room_ready(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)
        if not room:
            await self.send_error(ws, "NOT_IN_ROOM", "Вы не в комнате")
            return
        is_ready = msg.payload.get("is_ready", True)
        room.set_ready(player_id, is_ready)
        await room.broadcast(Message(MessageType.ROOM_UPDATE, {
            "event": "player_ready",
            "players": [p.to_dict() for p in room.get_players_info()]
        }))
        if room.all_ready():
            room.start_game()
            state = room.get_game_state()
            await room.broadcast(Message(MessageType.GAME_START, {
                "board_size": room.board_size,
                "komi": room.komi,
                "rules": room.rules,
                "players": [p.to_dict() for p in room.get_players_info()],
                "initial_state": state
            }))
            logger.info(f"Game started in room {room.room_id}")

    async def handle_game_move(self, ws: WebSocketServerProtocol, msg: Message):
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
        bs = result["board_state"]
        if result.get("move"):
            bs["last_move"] = result["move"]
        await room.broadcast(Message.game_state(
            board_array=bs["board"], current_player=bs["current_player"],
            move_number=bs["move_number"], passes=bs["passes"],
            last_move=bs.get("last_move"),
            captures=bs.get("captures", {"black": 0, "white": 0})))
        if result.get("game_over"):
            await self._finalize_game(room, "two_passes")

    async def handle_game_pass(self, ws: WebSocketServerProtocol, msg: Message):
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
        await room.broadcast(Message(MessageType.GAME_PASS, {
            "move": result["move"],
            "board_state": result["board_state"]
        }))
        if result.get("game_over"):
            await self._finalize_game(room, "two_passes")

    async def handle_game_resign(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)
        if not room or room.status != "playing":
            return
        result = room.resign(player_id)
        await self._finalize_game(room, "resign", winner=result.get("winner"),
                                    result_text=f"{result['resigned_player']} сдался")

    async def handle_game_undo_request(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)
        if not room or room.status != "playing":
            return
        result = room.request_undo(player_id)
        if result["success"]:
            opponent_ws = room.players.get(result["opponent_id"])
            if opponent_ws:
                room.pending_undo = player_id
                room.pending_undo_target = result["opponent_id"]
                await opponent_ws.websocket.send(Message(MessageType.GAME_UNDO_REQUEST, {
                    "requester": result["requester"],
                    "move_number": msg.payload.get("move_number")
                }).to_json())
        else:
            await self.send_error(ws, "UNDO_FAILED", result.get("error", "Нельзя отменить"))

    async def handle_game_undo_response(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)
        if not room:
            return
        accepted = msg.payload.get("accepted", False)
        result = room.confirm_undo(accepted)
        if result["success"] and result.get("accepted"):
            await room.broadcast(Message(MessageType.GAME_STATE, result["board_state"]))
        else:
            # Уведомляем запросившего об отказе
            if room.pending_undo_target:
                requester = room.players.get(room.pending_undo_target)
                if requester:
                    await requester.websocket.send(Message(MessageType.GAME_UNDO_RESPONSE, {
                        "accepted": False
                    }).to_json())

    async def handle_room_leave(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.leave_room(player_id)
        if room:
            await room.broadcast(Message(MessageType.ROOM_UPDATE, {
                "event": "player_left",
                "players": [p.to_dict() for p in room.get_players_info()]
            }))

    async def handle_game_chat(self, ws: WebSocketServerProtocol, msg: Message):
        conn = self.connections[ws]
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)
        if room:
            text = msg.payload.get("text", "")
            room.chat_history.append({
                "sender": conn["name"], "text": text,
                "timestamp": datetime.now().isoformat()
            })
            await room.broadcast(Message.game_chat(conn["name"], text))

    async def disconnect(self, websocket: WebSocketServerProtocol):
        conn = self.connections.get(websocket)
        if not conn:
            return
        player_id = conn["player_id"]
        room = self.lobby.get_player_room(player_id)
        if room:
            # Если игра активна — завершаем
            game_over = room.handle_player_disconnect(player_id)
            if game_over:
                await room.broadcast(Message.game_over(
                    winner=game_over["winner"],
                    result=game_over["result"],
                    reason=game_over["reason"]
                ))
            else:
                await room.broadcast(Message(MessageType.ROOM_UPDATE, {
                    "event": "player_disconnected",
                    "players": [p.to_dict() for p in room.get_players_info()]
                }))
        self.lobby.leave_room(player_id)
        if player_id in self.players:
            del self.players[player_id]
        del self.connections[websocket]

    async def _finalize_game(self, room: GameRoom, reason: str,
                             winner: Optional[str] = None,
                             result_text: Optional[str] = None):
        """Унифицированное завершение игры. DRY."""
        room.status = "finished"
        score = room.calculate_score()
        sgf = ""
        if room.session and hasattr(room.session.game, 'get_sgf'):
            try:
                sgf = room.session.game.get_sgf()
            except Exception:
                pass

        if winner is None:
            if score:
                raw = score.get("winner", "unknown")
                if "Черные" in raw or "black" in raw.lower():
                    winner = "black"
                elif "Белые" in raw or "white" in raw.lower():
                    winner = "white"
                else:
                    winner = "draw"
                result_text = score.get("full_result", "Игра окончена")
            else:
                winner = "unknown"
                result_text = "Игра окончена"

        await room.broadcast(Message.game_over(
            winner=winner, result=result_text, reason=reason, sgf=sgf
        ))
        logger.info(f"Game over in room {room.room_id}: {winner} — {result_text}")

    async def send_error(self, ws: WebSocketServerProtocol, code: str, message: str):
        try:
            await ws.send(Message.error(code, message).to_json())
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="OS-GO Network Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = GameServer(host=args.host, port=args.port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped")

if __name__ == "__main__":
    main()
