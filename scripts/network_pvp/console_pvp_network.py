"""
OS-GO Console PvP Network Integration
======================================

Integration module that connects the existing console PvP system
with the network client. Provides the same interface as console_PVP.py
but routes moves through the network.

This module acts as a bridge between:
- Existing console UI (console_PVP.py style)
- Network client (client.py)
- Core Go engine (core_adapter.py)

Usage:
    from console_pvp_network import NetworkPvPGame
    
    game = NetworkPvPGame(server_url="ws://localhost:8765/ws")
    await game.run()

Future Integration:
    This module is designed to be easily wrapped by PySide6 GUI:
    
    class GUINetworkGame(QObject):
        move_made = Signal(dict)
        game_started = Signal()
        
        def __init__(self):
            self.network = NetworkPvPGame()
            self.network.on_move_made = self.move_made.emit
            self.network.on_game_started = self.game_started.emit
"""

import asyncio
import sys
import os
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum, auto

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from protocol import MessageType, MessageBuilder, Messages, GameSettings
from client import NetworkClient, ClientConfig, ClientState, ConsoleRenderer


class NetworkGamePhase(Enum):
    """Extended phases for network game flow."""
    CONNECTING = auto()
    LOBBY = auto()
    ROOM_SETUP = auto()
    WAITING_OPPONENT = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    DISCONNECTED = auto()


@dataclass
class NetworkGameCallbacks:
    """Callback interface for UI integration.
    
    All callbacks are optional. Used by both console and GUI frontends.
    """
    on_connect: Optional[Callable[[], None]] = None
    on_disconnect: Optional[Callable[[], None]] = None
    on_room_joined: Optional[Callable[[Dict], None]] = None
    on_game_started: Optional[Callable[[Dict], None]] = None
    on_move_made: Optional[Callable[[Dict], None]] = None
    on_turn_change: Optional[Callable[[str], None]] = None
    on_game_over: Optional[Callable[[Dict], None]] = None
    on_chat: Optional[Callable[[str, str], None]] = None
    on_error: Optional[Callable[[str], None]] = None
    on_state_sync: Optional[Callable[[Dict], None]] = None
    on_opponent_joined: Optional[Callable[[Dict], None]] = None
    on_opponent_left: Optional[Callable[[], None]] = None


class NetworkPvPGame:
    """High-level network PvP game controller.
    
    Provides same interface pattern as local PvP/PvE modes:
    - initialize() -> setup game
    - run() -> main loop
    - make_move() -> execute move
    - save_game() -> export SGF
    
    Designed for easy integration with both console and GUI.
    """
    
    def __init__(self, server_url: str = "ws://localhost:8765/ws",
                 username: str = "", callbacks: Optional[NetworkGameCallbacks] = None):
        self.server_url = server_url
        self.username = username
        self.callbacks = callbacks or NetworkGameCallbacks()
        
        # Internal client
        config = ClientConfig(server_url=server_url, username=username)
        self.client = NetworkClient(config)
        
        # Override client handlers to inject our callbacks
        self._setup_callbacks()
        
        # Game state
        self.phase = NetworkGamePhase.DISCONNECTED
        self.my_color: Optional[str] = None
        self.current_turn: str = "black"
        self.board_size: int = 19
        self.moves: list = []
        self.room_id: Optional[str] = None
        
    def _setup_callbacks(self) -> None:
        """Wire client events to our callbacks."""
        original_handlers = self.client._message_handlers.copy()
        
        async def wrapped_connected(msg):
            await original_handlers[MessageType.CONNECTED.value](msg)
            self.phase = NetworkGamePhase.LOBBY
            if self.callbacks.on_connect:
                self.callbacks.on_connect()
        
        async def wrapped_room_joined(msg):
            await original_handlers[MessageType.ROOM_JOINED.value](msg)
            self.phase = NetworkGamePhase.WAITING_OPPONENT
            self.my_color = self.client.game_data.my_color
            self.board_size = self.client.game_data.board_size
            if self.callbacks.on_room_joined:
                self.callbacks.on_room_joined(msg.get("room", {}))
        
        async def wrapped_game_start(msg):
            await original_handlers[MessageType.GAME_START.value](msg)
            self.phase = NetworkGamePhase.PLAYING
            self.current_turn = "black"
            if self.callbacks.on_game_started:
                self.callbacks.on_game_started(msg)
        
        async def wrapped_move_made(msg):
            await original_handlers[MessageType.MOVE_MADE.value](msg)
            self.current_turn = self.client.game_data.current_turn
            if self.callbacks.on_move_made:
                self.callbacks.on_move_made(msg)
            if self.callbacks.on_turn_change:
                self.callbacks.on_turn_change(self.current_turn)
        
        async def wrapped_game_over(msg):
            await original_handlers[MessageType.GAME_OVER.value](msg)
            self.phase = NetworkGamePhase.GAME_OVER
            if self.callbacks.on_game_over:
                self.callbacks.on_game_over(msg)
        
        async def wrapped_chat(msg):
            await original_handlers[MessageType.CHAT.value](msg)
            if self.callbacks.on_chat:
                self.callbacks.on_chat(
                    msg.get("player", "Unknown"),
                    msg.get("text", "")
                )
        
        async def wrapped_error(msg):
            await original_handlers[MessageType.ERROR.value](msg)
            if self.callbacks.on_error:
                self.callbacks.on_error(msg.get("description", "Unknown error"))
        
        async def wrapped_player_joined(msg):
            await original_handlers[MessageType.PLAYER_JOINED.value](msg)
            if self.callbacks.on_opponent_joined:
                self.callbacks.on_opponent_joined(msg.get("player", {}))
        
        async def wrapped_player_left(msg):
            await original_handlers[MessageType.PLAYER_LEFT.value](msg)
            if self.callbacks.on_opponent_left:
                self.callbacks.on_opponent_left()
        
        # Replace handlers
        self.client._message_handlers[MessageType.CONNECTED.value] = wrapped_connected
        self.client._message_handlers[MessageType.ROOM_JOINED.value] = wrapped_room_joined
        self.client._message_handlers[MessageType.GAME_START.value] = wrapped_game_start
        self.client._message_handlers[MessageType.MOVE_MADE.value] = wrapped_move_made
        self.client._message_handlers[MessageType.GAME_OVER.value] = wrapped_game_over
        self.client._message_handlers[MessageType.CHAT.value] = wrapped_chat
        self.client._message_handlers[MessageType.ERROR.value] = wrapped_error
        self.client._message_handlers[MessageType.PLAYER_JOINED.value] = wrapped_player_joined
        self.client._message_handlers[MessageType.PLAYER_LEFT.value] = wrapped_player_left
    
    async def initialize(self) -> bool:
        """Initialize connection to server. Same pattern as local PvP init."""
        self.phase = NetworkGamePhase.CONNECTING
        return await self.client.connect()
    
    async def create_room(self, name: str, settings: GameSettings, 
                         password: Optional[str] = None) -> None:
        """Create a game room."""
        msg = Messages.create_room(name, settings, password)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def join_room(self, room_id: str, password: Optional[str] = None) -> None:
        """Join an existing room."""
        msg = Messages.join_room(room_id, password)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def set_ready(self) -> None:
        """Signal ready to start."""
        msg = Messages.create(MessageType.READY)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def make_move(self, x: int, y: int) -> None:
        """Place a stone. Same interface as local PvP."""
        if not self.my_color:
            raise ValueError("Not in a game")
        if self.current_turn != self.my_color:
            raise ValueError("Not your turn")
        
        msg = Messages.make_move(x, y, self.my_color)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def pass_turn(self) -> None:
        """Pass turn."""
        msg = Messages.create(MessageType.PASS)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def resign(self) -> None:
        """Resign game."""
        msg = Messages.create(MessageType.RESIGN)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def send_chat(self, text: str) -> None:
        """Send chat message."""
        msg = Messages.chat(text)
        await self.client.websocket.send(MessageBuilder.serialize(msg))
    
    async def save_game(self, filename: Optional[str] = None) -> str:
        """Save game to SGF. Returns filename."""
        return self.client._save_game()
    
    async def run(self) -> None:
        """Main game loop. Delegates to client run."""
        await self.client.run()
    
    async def disconnect(self) -> None:
        """Clean disconnect."""
        await self.client.disconnect()
        self.phase = NetworkGamePhase.DISCONNECTED
        if self.callbacks.on_disconnect:
            self.callbacks.on_disconnect()
    
    @property
    def is_my_turn(self) -> bool:
        """Check if it's our turn."""
        return self.current_turn == self.my_color
    
    @property
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.client.state != ClientState.DISCONNECTED


# ============================================================================
# CONSOLE INTERFACE (Same as console_PVP.py)
# ============================================================================

class ConsoleNetworkPvP:
    """Console interface matching existing console_PVP.py pattern."""
    
    def __init__(self, server_url: str = "ws://localhost:8765/ws"):
        self.renderer = ConsoleRenderer()
        self.game: Optional[NetworkPvPGame] = None
        self.server_url = server_url
        
    async def run(self) -> None:
        """Main entry point matching console_PVP.py interface."""
        self.renderer.print_header("OS-GO Network PvP")
        
        # Get username
        username = input("Enter your username: ").strip()
        
        # Initialize network game
        self.game = NetworkPvPGame(
            server_url=self.server_url,
            username=username,
            callbacks=NetworkGameCallbacks(
                on_connect=self._on_connect,
                on_room_joined=self._on_room_joined,
                on_game_started=self._on_game_started,
                on_move_made=self._on_move_made,
                on_game_over=self._on_game_over,
                on_chat=self._on_chat,
                on_error=self._on_error,
            )
        )
        
        # Connect
        if not await self.game.initialize():
            self.renderer.print_error("Failed to connect to server")
            return
        
        # Run main loop
        await self.game.run()
    
    def _on_connect(self) -> None:
        """Handle successful connection."""
        self.renderer.print_system_message("Connected to server!")
        self._show_lobby_menu()
    
    def _on_room_joined(self, room_data: Dict) -> None:
        """Handle room join."""
        self.renderer.print_room_info(room_data)
        self.renderer.print_system_message("Type 'ready' to start, 'leave' to exit")
    
    def _on_game_started(self, msg: Dict) -> None:
        """Handle game start."""
        self.renderer.print_header("Game Started!")
        self._render_board()
        self.renderer.print_help()
    
    def _on_move_made(self, move_data: Dict) -> None:
        """Handle move."""
        self._render_board()
        if self.game.is_my_turn:
            self.renderer.print_system_message("Your turn!")
    
    def _on_game_over(self, msg: Dict) -> None:
        """Handle game end."""
        winner = msg.get("winner", "none")
        self.renderer.print_header(f"Game Over - Winner: {winner}")
    
    def _on_chat(self, username: str, text: str) -> None:
        """Handle chat."""
        self.renderer.print_chat_message(username, text)
    
    def _on_error(self, error_msg: str) -> None:
        """Handle error."""
        self.renderer.print_error(error_msg)
    
    def _render_board(self) -> None:
        """Render current board state."""
        self.renderer.print_board(
            self.game.board_size,
            self.game.client.game_data.moves,
            self.game.my_color
        )
    
    def _show_lobby_menu(self) -> None:
        """Show lobby options."""
        self.renderer.print_lobby_menu()


async def main():
    """Entry point for console network PvP."""
    console = ConsoleNetworkPvP()
    await console.run()


if __name__ == "__main__":
    asyncio.run(main())
