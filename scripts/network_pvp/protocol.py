"""
OS-GO Network PvP Protocol
==========================

Shared message types and data structures for WebSocket communication.
Used by both server and client to ensure protocol consistency.

Message Format:
All messages are JSON objects with at least a 'type' field.

Author: OS-GO Development Team
Version: 1.0.0
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import json


class MessageType(str, Enum):
    """All possible message types in the protocol."""
    # Connection & Lobby
    CONNECT = "connect"           # Client -> Server: initial connection with auth
    CONNECTED = "connected"      # Server -> Client: connection confirmed
    DISCONNECT = "disconnect"      # Client -> Server: intentional disconnect
    
    # Room Management
    CREATE_ROOM = "create_room"    # Client -> Server: create new game room
    ROOM_CREATED = "room_created"   # Server -> Client: room created successfully
    JOIN_ROOM = "join_room"        # Client -> Server: join existing room
    ROOM_JOINED = "room_joined"    # Server -> Client: joined room successfully
    LEAVE_ROOM = "leave_room"      # Client -> Server: leave current room
    ROOM_LEFT = "room_left"        # Server -> Client: left room
    
    # Room State
    ROOM_LIST = "room_list"        # Server -> Client: list of available rooms
    ROOM_UPDATE = "room_update"     # Server -> Client: room state changed
    PLAYER_JOINED = "player_joined" # Server -> Client: another player joined
    PLAYER_LEFT = "player_left"    # Server -> Client: another player left
    
    # Game Setup
    GAME_START = "game_start"      # Server -> Client: game begins
    READY = "ready"                # Client -> Server: player ready to start
    
    # Gameplay
    MAKE_MOVE = "make_move"        # Client -> Server: place a stone
    MOVE_MADE = "move_made"        # Server -> Client: move validated and applied
    INVALID_MOVE = "invalid_move"  # Server -> Client: move rejected
    
    # Game Control
    PASS = "pass"                  # Client -> Server: pass turn
    RESIGN = "resign"              # Client -> Server: resign game
    GAME_OVER = "game_over"        # Server -> Client: game ended
    
    # State Sync
    SYNC_REQUEST = "sync_request"  # Client -> Server: request full state
    SYNC_STATE = "sync_state"      # Server -> Client: full game state
    
    # Chat
    CHAT = "chat"                  # Bidirectional: chat message
    
    # Error
    ERROR = "error"                # Server -> Client: error occurred
    PING = "ping"                  # Keep-alive
    PONG = "pong"                  # Keep-alive response


@dataclass
class GameSettings:
    """Game configuration shared between players."""
    board_size: int = 19            # 9, 13, or 19
    rules: str = "chinese"          # "chinese" or "japanese"
    komi: float = 7.5               # Compensation points
    handicap: int = 0               # Handicap stones
    time_limit: Optional[int] = None  # Seconds per player (None = no limit)
    byo_yomi: Optional[int] = None   # Byo-yomi periods
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_size": self.board_size,
            "rules": self.rules,
            "komi": self.komi,
            "handicap": self.handicap,
            "time_limit": self.time_limit,
            "byo_yomi": self.byo_yomi,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameSettings":
        return cls(**data)


@dataclass 
class PlayerInfo:
    """Public player information."""
    id: str
    username: str
    rating: int = 0
    color: Optional[str] = None     # "black" or "white", assigned in room
    ready: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "rating": self.rating,
            "color": self.color,
            "ready": self.ready,
        }


@dataclass
class RoomInfo:
    """Room information for lobby listing."""
    id: str
    name: str
    host: PlayerInfo
    settings: GameSettings
    players: List[PlayerInfo] = field(default_factory=list)
    status: str = "waiting"         # "waiting", "playing", "finished"
    password_protected: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host.to_dict(),
            "settings": self.settings.to_dict(),
            "players": [p.to_dict() for p in self.players],
            "status": self.status,
            "password_protected": self.password_protected,
        }


class MessageBuilder:
    """Helper class to build protocol messages."""
    
    @staticmethod
    def create(msg_type: MessageType, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a message with the given type and payload."""
        message = {"type": msg_type.value}
        if payload:
            message.update(payload)
        return message
    
    @staticmethod
    def parse(raw_message: str) -> Dict[str, Any]:
        """Parse a raw JSON message."""
        return json.loads(raw_message)
    
    @staticmethod
    def serialize(message: Dict[str, Any]) -> str:
        """Serialize a message to JSON string."""
        return json.dumps(message, ensure_ascii=False)


# Pre-built message helpers for common operations
class Messages:
    """Convenience methods for creating standard messages."""
    
    @staticmethod
    def connect(token: str, username: str) -> Dict[str, Any]:
        return MessageBuilder.create(MessageType.CONNECT, {
            "token": token,
            "username": username,
        })
    
    @staticmethod
    def create_room(name: str, settings: GameSettings, password: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "name": name,
            "settings": settings.to_dict(),
        }
        if password:
            payload["password"] = password
        return MessageBuilder.create(MessageType.CREATE_ROOM, payload)
    
    @staticmethod
    def join_room(room_id: str, password: Optional[str] = None) -> Dict[str, Any]:
        payload = {"room_id": room_id}
        if password:
            payload["password"] = password
        return MessageBuilder.create(MessageType.JOIN_ROOM, payload)
    
    @staticmethod
    def make_move(x: int, y: int, color: str) -> Dict[str, Any]:
        return MessageBuilder.create(MessageType.MAKE_MOVE, {
            "x": x,
            "y": y,
            "color": color,
        })
    
    @staticmethod
    def chat(text: str) -> Dict[str, Any]:
        return MessageBuilder.create(MessageType.CHAT, {"text": text})
    
    @staticmethod
    def error(code: str, description: str) -> Dict[str, Any]:
        return MessageBuilder.create(MessageType.ERROR, {
            "code": code,
            "description": description,
        })
    
    @staticmethod
    def move_made(x: int, y: int, color: str, move_number: int, 
                  captured: Optional[List[tuple]] = None) -> Dict[str, Any]:
        payload = {
            "x": x,
            "y": y,
            "color": color,
            "move_number": move_number,
        }
        if captured:
            payload["captured"] = captured
        return MessageBuilder.create(MessageType.MOVE_MADE, payload)
    
    @staticmethod
    def game_over(winner: Optional[str], reason: str, 
                   score_black: Optional[float] = None,
                   score_white: Optional[float] = None) -> Dict[str, Any]:
        payload = {
            "winner": winner,
            "reason": reason,
        }
        if score_black is not None:
            payload["score_black"] = score_black
        if score_white is not None:
            payload["score_white"] = score_white
        return MessageBuilder.create(MessageType.GAME_OVER, payload)
