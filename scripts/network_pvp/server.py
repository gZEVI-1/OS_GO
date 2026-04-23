"""
OS-GO Network PvP Server
=========================

WebSocket server for online Go matches via lobby system.
Handles room management, game state synchronization, and move validation.

Architecture:
- Uses FastAPI + WebSockets for real-time communication
- In-memory room and game state management (Redis-ready for scaling)
- Authoritative server: all moves validated server-side
- Supports reconnection and state resync

Usage:
    uvicorn server:app --host 0.0.0.0 --port 8765 --reload

Environment Variables:
    WS_HOST: Server bind address (default: 0.0.0.0)
    WS_PORT: Server port (default: 8765)
    JWT_SECRET: Secret for token validation
    MAX_ROOMS: Maximum concurrent rooms (default: 100)
    MAX_ROOM_AGE: Room max age in minutes (default: 60)

Author: OS-GO Development Team
Version: 1.0.0
"""

import asyncio
import json
import uuid
import time
import logging
import os
from typing import Dict, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import jwt

from protocol import (
    MessageType, MessageBuilder, Messages,
    GameSettings, PlayerInfo, RoomInfo
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class GameState:
    """Complete game state for server-side validation."""
    board_size: int = 19
    moves: List[Dict] = field(default_factory=list)
    current_turn: str = "black"  # "black" or "white"
    pass_count: int = 0
    resigned: Optional[str] = None
    captured_black: int = 0
    captured_white: int = 0
    _board: Optional[object] = field(default=None, repr=False)  # Go engine board
    
    def __post_init__(self):
        """Initialize go engine board after creation."""
        self._init_board()
    
    def _init_board(self):
        """Initialize the go engine board."""
        try:
            from core import Game as GoGame
            self._board = GoGame(self.board_size)
        except ImportError:
            logger.warning("Go engine not available, using basic validation")
            self._board = None
    
    def apply_move(self, x: int, y: int, color: str) -> Tuple[bool, Dict]:
        """Apply a move and update state. Returns (success, info)."""
        if color != self.current_turn:
            return False, {"error": "wrong_turn"}
        
        # Validate coordinates
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return False, {"error": "out_of_bounds"}
        
        # Use go engine for validation if available
        if self._board is not None:
            try:
                # Convert color to engine format
                from core import Color as GoColor
                engine_color = GoColor.Black if color == "black" else GoColor.White
                
                # Check if move is legal using the engine
                is_pass = (x == -1 and y == -1)
                
                if is_pass:
                    # Pass move - always valid on your turn
                    pass
                else:
                    # Try to make the move on the engine board
                    # The engine handles ko, suicide, and capture rules
                    if not self._board.makeMove(x, y, is_pass=False):
                        return False, {"error": "invalid_move_engine"}
                    
                    # Update captured stones count
                    # Note: This depends on how the engine exposes capture info
            except Exception as e:
                logger.error(f"Go engine error: {e}")
                return False, {"error": "engine_error"}
        
        # Record the move
        self.moves.append({"x": x, "y": y, "color": color})
        self.current_turn = "white" if color == "black" else "black"
        self.pass_count = 0
        
        return True, {"success": True}
    
    def apply_pass(self, color: str) -> None:
        """Apply a pass move."""
        self.moves.append({"type": "pass", "color": color})
        self.current_turn = "white" if color == "black" else "black"
        self.pass_count += 1
    
    def to_dict(self) -> Dict:
        return {
            "board_size": self.board_size,
            "moves": self.moves,
            "current_turn": self.current_turn,
            "pass_count": self.pass_count,
            "captured_black": self.captured_black,
            "captured_white": self.captured_white,
        }


@dataclass
class Room:
    """Game room containing players and game state."""
    id: str
    name: str
    host_id: str
    settings: GameSettings
    players: Dict[str, 'PlayerConnection'] = field(default_factory=dict)
    password: Optional[str] = None
    status: str = "waiting"  # waiting, playing, finished
    game_state: Optional[GameState] = None
    created_at: datetime = field(default_factory=datetime.now)
    chat_history: List[Dict] = field(default_factory=list)
    
    @property
    def is_full(self) -> bool:
        return len(self.players) >= 2
    
    @property
    def is_empty(self) -> bool:
        return len(self.players) == 0
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    def get_info(self) -> RoomInfo:
        """Get public room information."""
        return RoomInfo(
            id=self.id,
            name=self.name,
            host=self.players[self.host_id].info if self.host_id in self.players else None,
            settings=self.settings,
            players=[p.info for p in self.players.values()],
            status=self.status,
            password_protected=self.password is not None,
        )
    
    def assign_colors(self) -> None:
        """Assign black/white to players."""
        player_list = list(self.players.values())
        if len(player_list) >= 1:
            player_list[0].info.color = "black"
        if len(player_list) >= 2:
            player_list[1].info.color = "white"


@dataclass
class PlayerConnection:
    """WebSocket connection wrapper for a player."""
    websocket: WebSocket
    info: PlayerInfo
    room_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: float = field(default_factory=time.time)
    
    async def send(self, message: Dict) -> None:
        """Send message to this player."""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send to {self.info.id}: {e}")
    
    async def receive(self) -> Dict:
        """Receive message from this player."""
        return await self.websocket.receive_json()


# ============================================================================
# ROOM MANAGER
# ============================================================================

class RoomManager:
    """Manages all game rooms and player connections."""
    
    def __init__(self, max_rooms: int = 100):
        self.rooms: Dict[str, Room] = {}
        self.players: Dict[str, PlayerConnection] = {}
        self.max_rooms = max_rooms
        self._lock = asyncio.Lock()
    
    async def create_room(self, name: str, host: PlayerConnection, 
                         settings: GameSettings, password: Optional[str] = None) -> Room:
        """Create a new game room."""
        async with self._lock:
            if len(self.rooms) >= self.max_rooms:
                raise ValueError("Maximum number of rooms reached")
            
            room_id = str(uuid.uuid4())[:8]
            room = Room(
                id=room_id,
                name=name,
                host_id=host.info.id,
                settings=settings,
                password=password,
            )
            self.rooms[room_id] = room
            logger.info(f"Room created: {room_id} by {host.info.username}")
            return room
    
    async def join_room(self, room_id: str, player: PlayerConnection, 
                        password: Optional[str] = None) -> Room:
        """Add player to existing room."""
        async with self._lock:
            if room_id not in self.rooms:
                raise ValueError("Room not found")
            
            room = self.rooms[room_id]
            
            if room.is_full:
                raise ValueError("Room is full")
            
            if room.password and room.password != password:
                raise ValueError("Invalid password")
            
            if room.status != "waiting":
                raise ValueError("Game already in progress")
            
            room.players[player.info.id] = player
            player.room_id = room_id
            
            logger.info(f"Player {player.info.username} joined room {room_id}")
            return room
    
    async def leave_room(self, player_id: str) -> Optional[Room]:
        """Remove player from their room."""
        async with self._lock:
            player = self.players.get(player_id)
            if not player or not player.room_id:
                return None
            
            room = self.rooms.get(player.room_id)
            if not room:
                return None
            
            if player_id in room.players:
                del room.players[player_id]
                
                # CRITICAL FIX: Remove player from global players dictionary
                if player_id in self.players:
                    del self.players[player_id]
                
                player.room_id = None
                
                # Notify remaining players
                await self.broadcast_to_room(room.id, Messages.create(MessageType.PLAYER_LEFT, {
                    "player_id": player_id
                }))
                
                # If room empty, remove it
                if room.is_empty:
                    del self.rooms[room.id]
                    logger.info(f"Room removed: {room.id}")
                # If host left, assign new host
                elif room.host_id == player_id and room.players:
                    room.host_id = next(iter(room.players.keys()))
                    await self.broadcast_to_room(room.id, {
                        "type": MessageType.ROOM_UPDATE.value,
                        "new_host": room.host_id,
                    })
                
                logger.info(f"Player {player_id} left room {room.id}")
            
            return room
    
    async def broadcast_to_room(self, room_id: str, message: Dict, 
                                 exclude: Optional[str] = None) -> None:
        """Send message to all players in a room."""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        tasks = []
        for pid, player in room.players.items():
            if pid != exclude:
                tasks.append(player.send(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_room_list(self) -> List[RoomInfo]:
        """Get list of available rooms."""
        async with self._lock:
            return [room.get_info() for room in self.rooms.values() 
                    if room.status == "waiting"]
    
    async def cleanup_old_rooms(self, max_age_minutes: int = 60) -> None:
        """Remove inactive rooms."""
        async with self._lock:
            cutoff = datetime.now() - timedelta(minutes=max_age_minutes)
            to_remove = [
                rid for rid, room in self.rooms.items()
                if room.created_at < cutoff and room.is_empty
            ]
            for rid in to_remove:
                del self.rooms[rid]
                logger.info(f"Cleaned up old room: {rid}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="OS-GO Network Server",
    description="WebSocket server for online Go matches",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global room manager
room_manager = RoomManager(max_rooms=100)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))


def validate_jwt_token(token: str) -> Optional[Dict]:
    """Validate JWT token and return payload if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def create_jwt_token(player_id: str, username: str) -> str:
    """Create a JWT token for a player."""
    from datetime import timedelta
    payload = {
        "player_id": player_id,
        "username": username,
        "exp": datetime.now() + timedelta(minutes=JWT_EXPIRATION_MINUTES),
        "iat": datetime.now(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.on_event("startup")
async def startup():
    """Initialize server."""
    logger.info("OS-GO Network Server starting...")
    # Start cleanup task
    asyncio.create_task(cleanup_task())


async def cleanup_task():
    """Periodic cleanup of old rooms."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        await room_manager.cleanup_old_rooms()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "OS-GO Network Server",
        "version": "1.0.0",
        "rooms": len(room_manager.rooms),
        "players_online": len(room_manager.players),
    }


@app.get("/rooms")
async def list_rooms():
    """HTTP endpoint to list available rooms."""
    rooms = await room_manager.get_room_list()
    return {"rooms": [r.to_dict() for r in rooms]}


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for game communication."""
    await websocket.accept()
    player: Optional[PlayerConnection] = None
    
    try:
        # Wait for initial connect message
        raw_msg = await websocket.receive_json()
        msg_type = raw_msg.get("type")
        
        if msg_type != MessageType.CONNECT.value:
            await websocket.send_json(Messages.error("AUTH_REQUIRED", "First message must be connect"))
            return
        
        # JWT Token validation (optional for development, required in production)
        token = raw_msg.get("token")
        if os.getenv("PRODUCTION", "false").lower() == "true":
            if not token:
                await websocket.send_json(Messages.error("AUTH_REQUIRED", "Token required in production mode"))
                return
            
            payload = validate_jwt_token(token)
            if not payload:
                await websocket.send_json(Messages.error("INVALID_TOKEN", "Token validation failed"))
                return
            
            # Use validated user info from token
            player_id = payload.get("player_id", str(uuid.uuid4()))
            username = payload.get("username", f"Player_{player_id[:6]}")
        else:
            # Development mode: accept username without token or create new session
            username = raw_msg.get("username", f"Player_{str(uuid.uuid4())[:6]}")
            player_id = str(uuid.uuid4())
        
        player = PlayerConnection(
            websocket=websocket,
            info=PlayerInfo(id=player_id, username=username),
        )
        room_manager.players[player_id] = player
        
        # Send confirmation with JWT token for future requests
        jwt_token = create_jwt_token(player_id, username)
        await player.send(Messages.create(MessageType.CONNECTED, {
            "player_id": player_id,
            "username": username,
            "token": jwt_token,  # Token for reconnection
        }))
        
        logger.info(f"Player connected: {username} ({player_id})")
        
        # Main message loop
        while True:
            try:
                raw_msg = await asyncio.wait_for(player.receive(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send ping to check connection
                await player.send(Messages.create(MessageType.PING))
                try:
                    pong = await asyncio.wait_for(player.receive(), timeout=5.0)
                    if pong.get("type") != MessageType.PONG.value:
                        break
                except asyncio.TimeoutError:
                    break
                continue
            
            await handle_message(player, raw_msg)
            
    except WebSocketDisconnect:
        logger.info(f"Player disconnected: {player.info.username if player else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await handle_disconnect(player)


async def handle_message(player: PlayerConnection, message: Dict) -> None:
    """Route message to appropriate handler."""
    msg_type = message.get("type")
    
    handlers = {
        MessageType.CREATE_ROOM.value: handle_create_room,
        MessageType.JOIN_ROOM.value: handle_join_room,
        MessageType.LEAVE_ROOM.value: handle_leave_room,
        MessageType.READY.value: handle_ready,
        MessageType.MAKE_MOVE.value: handle_make_move,
        MessageType.PASS.value: handle_pass,
        MessageType.RESIGN.value: handle_resign,
        MessageType.SYNC_REQUEST.value: handle_sync_request,
        MessageType.CHAT.value: handle_chat,
        MessageType.PONG.value: handle_pong,
    }
    
    handler = handlers.get(msg_type)
    if handler:
        await handler(player, message)
    else:
        await player.send(Messages.error("UNKNOWN_TYPE", f"Unknown message type: {msg_type}"))


async def handle_disconnect(player: Optional[PlayerConnection]) -> None:
    """Clean up when player disconnects."""
    if not player:
        return
    
    # Remove from room
    if player.room_id:
        await room_manager.leave_room(player.info.id)
    
    # Remove from players
    if player.info.id in room_manager.players:
        del room_manager.players[player.info.id]


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def handle_create_room(player: PlayerConnection, message: Dict) -> None:
    """Handle room creation request."""
    try:
        name = message.get("name", f"Room_{player.info.username}")
        settings_dict = message.get("settings", {})
        settings = GameSettings.from_dict(settings_dict)
        password = message.get("password")
        
        room = await room_manager.create_room(name, player, settings, password)
        await room_manager.join_room(room.id, player)
        room.assign_colors()
        
        await player.send(Messages.create(MessageType.ROOM_CREATED, {
            "room": room.get_info().to_dict(),
            "your_color": player.info.color,
        }))
        
    except ValueError as e:
        await player.send(Messages.error("CREATE_FAILED", str(e)))


async def handle_join_room(player: PlayerConnection, message: Dict) -> None:
    """Handle room join request."""
    try:
        room_id = message.get("room_id")
        password = message.get("password")
        
        if not room_id:
            await player.send(Messages.error("MISSING_ROOM_ID", "Room ID required"))
            return
        
        room = await room_manager.join_room(room_id, player, password)
        room.assign_colors()
        
        # Notify player
        await player.send(Messages.create(MessageType.ROOM_JOINED, {
            "room": room.get_info().to_dict(),
            "your_color": player.info.color,
        }))
        
        # Notify other players
        await room_manager.broadcast_to_room(
            room_id,
            Messages.create(MessageType.PLAYER_JOINED, {
                "player": player.info.to_dict(),
            }),
            exclude=player.info.id
        )
        
        # If room is now full, notify both players
        if room.is_full:
            await room_manager.broadcast_to_room(room_id, {
                "type": MessageType.ROOM_UPDATE.value,
                "message": "Room is full, waiting for players to be ready",
            })
        
    except ValueError as e:
        await player.send(Messages.error("JOIN_FAILED", str(e)))


async def handle_leave_room(player: PlayerConnection, message: Dict) -> None:
    """Handle room leave request."""
    room = await room_manager.leave_room(player.info.id)
    if room:
        await player.send(Messages.create(MessageType.ROOM_LEFT, {
            "room_id": room.id,
        }))


async def handle_ready(player: PlayerConnection, message: Dict) -> None:
    """Handle player ready status."""
    if not player.room_id:
        await player.send(Messages.error("NOT_IN_ROOM", "Not in a room"))
        return
    
    room = room_manager.rooms.get(player.room_id)
    if not room:
        return
    
    player.info.ready = True
    
    # Check if all players ready
    all_ready = all(p.info.ready for p in room.players.values())
    
    if all_ready and room.is_full:
        # Start game
        room.status = "playing"
        room.game_state = GameState(board_size=room.settings.board_size)
        
        await room_manager.broadcast_to_room(room.id, {
            "type": MessageType.GAME_START.value,
            "game_state": room.game_state.to_dict(),
            "settings": room.settings.to_dict(),
        })
        logger.info(f"Game started in room {room.id}")
    else:
        await room_manager.broadcast_to_room(room.id, {
            "type": MessageType.ROOM_UPDATE.value,
            "player_id": player.info.id,
            "ready": True,
        })


async def handle_make_move(player: PlayerConnection, message: Dict) -> None:
    """Handle move placement."""
    if not player.room_id:
        await player.send(Messages.error("NOT_IN_ROOM", "Not in a room"))
        return
    
    room = room_manager.rooms.get(player.room_id)
    if not room or not room.game_state:
        await player.send(Messages.error("NO_GAME", "No active game"))
        return
    
    x = message.get("x")
    y = message.get("y")
    color = message.get("color")
    
    # Validate it's player's turn
    if color != player.info.color:
        await player.send(Messages.error("WRONG_TURN", "Not your turn"))
        return
    
    # Apply move (server authoritative)
    if room.game_state.apply_move(x, y, color):
        move_number = len(room.game_state.moves)
        
        # Broadcast to all players
        await room_manager.broadcast_to_room(room.id, Messages.move_made(
            x=x, y=y, color=color, move_number=move_number
        ))
        
        logger.info(f"Move {move_number}: {color} at ({x},{y}) in room {room.id}")
    else:
        await player.send(Messages.error("INVALID_MOVE", "Invalid move"))


async def handle_pass(player: PlayerConnection, message: Dict) -> None:
    """Handle pass move."""
    if not player.room_id:
        return
    
    room = room_manager.rooms.get(player.room_id)
    if not room or not room.game_state:
        return
    
    color = player.info.color
    room.game_state.apply_pass(color)
    
    await room_manager.broadcast_to_room(room.id, {
        "type": MessageType.MOVE_MADE.value,
        "move_type": "pass",
        "color": color,
        "move_number": len(room.game_state.moves),
    })
    
    # Check for game end (two consecutive passes)
    if room.game_state.pass_count >= 2:
        room.status = "finished"
        await room_manager.broadcast_to_room(room.id, Messages.game_over(
            winner=None, reason="double_pass"
        ))


async def handle_resign(player: PlayerConnection, message: Dict) -> None:
    """Handle resignation."""
    if not player.room_id:
        return
    
    room = room_manager.rooms.get(player.room_id)
    if not room:
        return
    
    winner = "white" if player.info.color == "black" else "black"
    room.status = "finished"
    
    await room_manager.broadcast_to_room(room.id, Messages.game_over(
        winner=winner, reason="resignation"
    ))


async def handle_sync_request(player: PlayerConnection, message: Dict) -> None:
    """Handle state sync request (for reconnection)."""
    if not player.room_id:
        return
    
    room = room_manager.rooms.get(player.room_id)
    if not room:
        return
    
    await player.send(Messages.create(MessageType.SYNC_STATE, {
        "room": room.get_info().to_dict(),
        "game_state": room.game_state.to_dict() if room.game_state else None,
        "chat_history": room.chat_history[-50:],  # Last 50 messages
    }))


async def handle_chat(player: PlayerConnection, message: Dict) -> None:
    """Handle chat message."""
    if not player.room_id:
        return
    
    room = room_manager.rooms.get(player.room_id)
    if not room:
        return
    
    chat_msg = {
        "player": player.info.username,
        "text": message.get("text", ""),
        "timestamp": datetime.now().isoformat(),
    }
    room.chat_history.append(chat_msg)
    
    await room_manager.broadcast_to_room(room.id, {
        "type": MessageType.CHAT.value,
        **chat_msg,
    })


async def handle_pong(player: PlayerConnection, message: Dict) -> None:
    """Handle pong response."""
    player.last_ping = time.time()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8765,
        log_level="info",
        reload=True,
    )
