"""
OS-GO Network Protocol v1.0
"""
import json
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import go_engine as go

class MessageType(Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    ROOM_LIST = "room_list"
    ROOM_CREATE = "room_create"
    ROOM_JOIN = "room_join"
    ROOM_LEAVE = "room_leave"
    ROOM_UPDATE = "room_update"
    ROOM_READY = "room_ready"
    GAME_START = "game_start"
    GAME_MOVE = "game_move"
    GAME_PASS = "game_pass"
    GAME_RESIGN = "game_resign"
    GAME_UNDO_REQUEST = "game_undo_request"
    GAME_UNDO_RESPONSE = "game_undo_response"
    GAME_STATE = "game_state"
    GAME_OVER = "game_over"
    GAME_CHAT = "game_chat"

class PlayerColor(Enum):
    BLACK = "black"
    WHITE = "white"
    SPECTATOR = "spectator"

@dataclass
class RoomInfo:
    room_id: str
    name: str
    host_name: str
    board_size: int
    has_password: bool
    player_count: int
    max_players: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "host_name": self.host_name,
            "board_size": self.board_size,
            "has_password": self.has_password,
            "player_count": self.player_count,
            "max_players": self.max_players,
            "status": self.status
        }

@dataclass
class PlayerInfo:
    player_id: str
    name: str
    color: Optional[str]
    is_ready: bool
    is_connected: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "color": self.color,
            "is_ready": self.is_ready,
            "is_connected": self.is_connected
        }

class Message:
    def __init__(self, msg_type: MessageType, payload: Dict[str, Any] = None):
        self.type = msg_type
        self.payload = payload or {}

    def to_json(self) -> str:
        return json.dumps({"type": self.type.value, "payload": self.payload})

    @classmethod
    def from_json(cls, data: str) -> "Message":
        parsed = json.loads(data)
        msg_type = MessageType(parsed["type"])
        return cls(msg_type, parsed.get("payload", {}))

    @classmethod
    def connect(cls, player_name: str, version: str = "1.0") -> "Message":
        return cls(MessageType.CONNECT, {"player_name": player_name, "version": version})

    @classmethod
    def error(cls, code: str, message: str) -> "Message":
        return cls(MessageType.ERROR, {"code": code, "message": message})

    @classmethod
    def room_list(cls, rooms: List[RoomInfo]) -> "Message":
        return cls(MessageType.ROOM_LIST, {"rooms": [r.to_dict() for r in rooms]})

    @classmethod
    def room_create(cls, name: str, board_size: int = 19, password: Optional[str] = None, komi: float = 6.5, rules: str = "japanese") -> "Message":
        return cls(MessageType.ROOM_CREATE, {"name": name, "board_size": board_size, "password": password, "komi": komi, "rules": rules})

    @classmethod
    def room_join(cls, room_id: str, password: Optional[str] = None) -> "Message":
        return cls(MessageType.ROOM_JOIN, {"room_id": room_id, "password": password})

    @classmethod
    def room_ready(cls, is_ready: bool = True) -> "Message":
        return cls(MessageType.ROOM_READY, {"is_ready": is_ready})

    @classmethod
    def game_move(cls, x: int, y: int, move_number: int) -> "Message":
        return cls(MessageType.GAME_MOVE, {"x": x, "y": y, "move_number": move_number})

    @classmethod
    def game_pass(cls, move_number: int) -> "Message":
        return cls(MessageType.GAME_PASS, {"move_number": move_number})

    @classmethod
    def game_resign(cls) -> "Message":
        return cls(MessageType.GAME_RESIGN)

    @classmethod
    def game_state(cls, board_array: List[List[int]], current_player: str, move_number: int, passes: int, last_move: Optional[Dict] = None, captures: Dict[str, int] = None) -> "Message":
        return cls(MessageType.GAME_STATE, {"board": board_array, "current_player": current_player, "move_number": move_number, "passes": passes, "last_move": last_move, "captures": captures or {"black": 0, "white": 0}})

    @classmethod
    def game_over(cls, winner: str, result: str, reason: str = "two_passes") -> "Message":
        return cls(MessageType.GAME_OVER, {"winner": winner, "result": result, "reason": reason})

    @classmethod
    def game_chat(cls, sender: str, text: str) -> "Message":
        return cls(MessageType.GAME_CHAT, {"sender": sender, "text": text})

    @classmethod
    def undo_request(cls, move_number: int) -> "Message":
        return cls(MessageType.GAME_UNDO_REQUEST, {"move_number": move_number})

    @classmethod
    def undo_response(cls, accepted: bool) -> "Message":
        return cls(MessageType.GAME_UNDO_RESPONSE, {"accepted": accepted})

class GameAction:
    @staticmethod
    def color_to_str(color: go.Color) -> str:
        return {go.Color.Black: "black", go.Color.White: "white", go.Color.NONE: "none"}.get(color, "none")

    @staticmethod
    def str_to_color(color_str: str) -> go.Color:
        return {"black": go.Color.Black, "white": go.Color.White, "none": go.Color.NONE}.get(color_str, go.Color.NONE)

    @staticmethod
    def board_to_array(board: go.Board) -> List[List[int]]:
        return board.get_board_array()

    @staticmethod
    def move_to_dict(move: go.Move) -> Dict[str, Any]:
        return {
            "x": move.pos.x if not move.is_pass else -1,
            "y": move.pos.y if not move.is_pass else -1,
            "color": GameAction.color_to_str(move.color),
            "move_number": move.move_number,
            "is_pass": move.is_pass
        }