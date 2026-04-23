"""
OS-GO Network PvP Console Client
=================================

Console-based client for online Go matches via WebSocket.
Provides the same interface as local PvP/PvE modes for consistency.

Features:
- Lobby browsing and room management
- Real-time gameplay with move validation
- Chat during matches
- Auto-reconnect and state synchronization
- SGF export of completed games

Usage:
    python client.py [server_url]
    
    Default server: ws://localhost:8765/ws

Controls:
    During lobby:
        1 - Create room        2 - Join room
        3 - List rooms         4 - Refresh
        q - Quit
    
    During game:
        Move: coordinates (e.g., 'd4', 'q16')
        Pass: 'pass' or 'p'
        Resign: 'resign' or 'r'
        Chat: 'chat <message>'
        Save: 'save'
        Quit: 'quit' or 'q'

Architecture:
    - Asyncio-based for non-blocking I/O
    - Separate tasks for: user input, server messages, rendering
    - State machine: disconnected -> lobby -> room -> playing -> finished
    - Compatible with future PySide6 GUI integration

Author: OS-GO Development Team
Version: 1.0.0
"""

import asyncio
import sys
import os
import json
import uuid
import argparse
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI

# Add parent directory to path for protocol import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import (
    MessageType, MessageBuilder, Messages,
    GameSettings, PlayerInfo
)


# ============================================================================
# CLIENT STATE MACHINE
# ============================================================================

class ClientState(Enum):
    """Client connection states."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    LOBBY = auto()
    IN_ROOM = auto()
    PLAYING = auto()
    FINISHED = auto()


@dataclass
class GameData:
    """Local game state mirror."""
    board_size: int = 19
    moves: List[Dict] = field(default_factory=list)
    current_turn: str = "black"
    my_color: Optional[str] = None
    opponent: Optional[PlayerInfo] = None
    
    def is_my_turn(self) -> bool:
        return self.current_turn == self.my_color


@dataclass
class ClientConfig:
    """Client configuration."""
    server_url: str = "ws://localhost:8765/ws"
    username: str = ""
    auto_reconnect: bool = True
    reconnect_delay: int = 5
    max_reconnect_attempts: int = 3


# ============================================================================
# CONSOLE RENDERER
# ============================================================================

class ConsoleRenderer:
    """Handles all console output for consistent UI."""
    
    @staticmethod
    def clear():
        """Clear console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_header(text: str):
        """Print section header."""
        print(f"\n{'='*50}")
        print(f"  {text}")
        print(f"{'='*50}\n")
    
    @staticmethod
    def print_board(board_size: int, moves: List[Dict], my_color: Optional[str] = None):
        """Print Go board in console."""
        # Initialize empty board
        board = [['.' for _ in range(board_size)] for _ in range(board_size)]
        
        # Place stones
        for move in moves:
            if 'x' in move and 'y' in move:
                x, y = move['x'], move['y']
                if 0 <= x < board_size and 0 <= y < board_size:
                    board[y][x] = 'X' if move['color'] == 'black' else 'O'
        
        # Print coordinates header
        cols = '    ' + ' '.join(chr(ord('A') + i) for i in range(board_size))
        print(cols)
        print("   +" + "-" * (board_size * 2 + 1))
        
        # Print rows
        for i in range(board_size):
            row_num = f"{board_size - i:2d} |"
            row_content = ' '.join(board[i])
            print(f"{row_num} {row_content} | {board_size - i:2d}")
        
        print("   +" + "-" * (board_size * 2 + 1))
        print(cols)
        print()
    
    @staticmethod
    def print_lobby_menu():
        """Print lobby menu options."""
        print("\n[LOBBY MENU]")
        print("  1. Create Room")
        print("  2. Join Room")
        print("  3. List Rooms")
        print("  4. Refresh")
        print("  q. Quit")
        print()
    
    @staticmethod
    def print_room_info(room_data: Dict):
        """Print room information."""
        print(f"\nRoom: {room_data.get('name', 'Unknown')}")
        print(f"ID: {room_data.get('id', 'N/A')}")
        print(f"Status: {room_data.get('status', 'unknown')}")
        print(f"Players: {len(room_data.get('players', []))}/2")
        
        settings = room_data.get('settings', {})
        print(f"Board: {settings.get('board_size', 19)}x{settings.get('board_size', 19)}")
        print(f"Rules: {settings.get('rules', 'chinese')}")
        print(f"Komi: {settings.get('komi', 7.5)}")
    
    @staticmethod
    def print_game_status(game_data: GameData, room_data: Optional[Dict] = None):
        """Print current game status."""
        print(f"\n[{'YOUR TURN' if game_data.is_my_turn() else 'OPPONENT TURN'}]")
        print(f"You: {game_data.my_color or 'unknown'}")
        print(f"Turn: {game_data.current_turn}")
        print(f"Moves: {len(game_data.moves)}")
        if room_data:
            players = room_data.get('players', [])
            for p in players:
                color = p.get('color', '?')
                name = p.get('username', 'Unknown')
                print(f"  {color}: {name}")
    
    @staticmethod
    def print_chat_message(username: str, text: str):
        """Print chat message."""
        print(f"\n[CHAT] {username}: {text}")
    
    @staticmethod
    def print_system_message(text: str):
        """Print system message."""
        print(f"\n[SYSTEM] {text}")
    
    @staticmethod
    def print_error(text: str):
        """Print error message."""
        print(f"\n[ERROR] {text}")
    
    @staticmethod
    def print_help():
        """Print game controls help."""
        print("\n[CONTROLS]")
        print("  Move:  coordinates (e.g., 'd4', 'q16')")
        print("  Pass:  'pass' or 'p'")
        print("  Resign: 'resign' or 'r'")
        print("  Chat:  'chat <message>'")
        print("  Save:  'save'")
        print("  Quit:  'quit' or 'q'")
        print()


# ============================================================================
# NETWORK CLIENT
# ============================================================================

class NetworkClient:
    """Main client class handling WebSocket connection and game logic."""
    
    def __init__(self, config: ClientConfig):
        self.config = config
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.state = ClientState.DISCONNECTED
        self.player_id: Optional[str] = None
        self.username: str = config.username or f"Player_{str(uuid.uuid4())[:6]}"
        self.current_room: Optional[Dict] = None
        self.game_data = GameData()
        self.available_rooms: List[Dict] = []
        self.renderer = ConsoleRenderer()
        self._message_handlers: Dict[str, Callable] = {
            MessageType.CONNECTED.value: self._handle_connected,
            MessageType.ROOM_CREATED.value: self._handle_room_created,
            MessageType.ROOM_JOINED.value: self._handle_room_joined,
            MessageType.ROOM_LEFT.value: self._handle_room_left,
            MessageType.ROOM_LIST.value: self._handle_room_list,
            MessageType.ROOM_UPDATE.value: self._handle_room_update,
            MessageType.PLAYER_JOINED.value: self._handle_player_joined,
            MessageType.PLAYER_LEFT.value: self._handle_player_left,
            MessageType.GAME_START.value: self._handle_game_start,
            MessageType.MOVE_MADE.value: self._handle_move_made,
            MessageType.INVALID_MOVE.value: self._handle_invalid_move,
            MessageType.GAME_OVER.value: self._handle_game_over,
            MessageType.SYNC_STATE.value: self._handle_sync_state,
            MessageType.CHAT.value: self._handle_chat,
            MessageType.ERROR.value: self._handle_error,
            MessageType.PING.value: self._handle_ping,
        }
        self._running = False
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._render_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to server."""
        try:
            self.state = ClientState.CONNECTING
            self.renderer.print_system_message(f"Connecting to {self.config.server_url}...")
            
            self.websocket = await websockets.connect(self.config.server_url)
            
            # Send connect message
            connect_msg = Messages.connect("", self.username)
            await self.websocket.send(MessageBuilder.serialize(connect_msg))
            
            self._running = True
            return True
            
        except (ConnectionRefusedError, InvalidURI, OSError) as e:
            self.renderer.print_error(f"Connection failed: {e}")
            self.state = ClientState.DISCONNECTED
            return False
    
    async def disconnect(self) -> None:
        """Close connection gracefully."""
        self._running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.websocket = None
        self.state = ClientState.DISCONNECTED
    
    async def run(self) -> None:
        """Main client loop."""
        if not await self.connect():
            return
        
        # Start concurrent tasks
        await asyncio.gather(
            self._receive_loop(),
            self._input_loop(),
            self._process_loop(),
            return_exceptions=True,
        )
    
    async def _receive_loop(self) -> None:
        """Handle incoming server messages."""
        try:
            async for message_raw in self.websocket:
                try:
                    message = MessageBuilder.parse(message_raw)
                    msg_type = message.get("type")
                    
                    handler = self._message_handlers.get(msg_type)
                    if handler:
                        await handler(message)
                    else:
                        self.renderer.print_system_message(f"Unhandled: {msg_type}")
                        
                except json.JSONDecodeError:
                    self.renderer.print_error("Invalid message format")
                    
        except ConnectionClosed:
            self.renderer.print_error("Connection closed by server")
        except Exception as e:
            self.renderer.print_error(f"Receive error: {e}")
        finally:
            self._running = False
    
    async def _input_loop(self) -> None:
        """Handle user input from console."""
        loop = asyncio.get_event_loop()
        
        while self._running:
            try:
                # Use asyncio.to_thread for non-blocking input
                user_input = await asyncio.wait_for(
                    loop.run_in_executor(None, input, self._get_prompt()),
                    timeout=0.5
                )
                await self._input_queue.put(user_input.strip())
                
            except asyncio.TimeoutError:
                continue
            except EOFError:
                break
    
    def _get_prompt(self) -> str:
        """Get input prompt based on current state."""
        if self.state == ClientState.LOBBY:
            return "[LOBBY] > "
        elif self.state == ClientState.IN_ROOM:
            return "[ROOM] > "
        elif self.state == ClientState.PLAYING:
            if self.game_data.is_my_turn():
                return "[YOUR MOVE] > "
            return "[WAITING] > "
        return "> "
    
    async def _process_loop(self) -> None:
        """Process user input and render updates."""
        while self._running:
            try:
                # Process input
                user_input = await asyncio.wait_for(
                    self._input_queue.get(), timeout=0.1
                )
                await self._handle_user_input(user_input)
                
            except asyncio.TimeoutError:
                # Check render queue
                try:
                    render_task = self._render_queue.get_nowait()
                    render_task()
                except asyncio.QueueEmpty:
                    pass
    
    async def _handle_user_input(self, user_input: str) -> None:
        """Route user input based on current state."""
        if not user_input:
            return
        
        # Global commands
        if user_input.lower() in ['quit', 'q', 'exit']:
            await self.disconnect()
            return
        
        # State-specific handling
        if self.state == ClientState.LOBBY:
            await self._handle_lobby_input(user_input)
        elif self.state == ClientState.IN_ROOM:
            await self._handle_room_input(user_input)
        elif self.state == ClientState.PLAYING:
            await self._handle_game_input(user_input)
    
    async def _handle_lobby_input(self, cmd: str) -> None:
        """Handle lobby commands."""
        if cmd == '1':
            await self._create_room_interactive()
        elif cmd == '2':
            await self._join_room_interactive()
        elif cmd == '3':
            await self._list_rooms()
        elif cmd == '4':
            self.renderer.clear()
            self.renderer.print_header("OS-GO Network Lobby")
            self.renderer.print_lobby_menu()
        else:
            self.renderer.print_error("Unknown command")
    
    async def _handle_room_input(self, cmd: str) -> None:
        """Handle room commands."""
        if cmd.lower() == 'ready':
            await self._send_ready()
        elif cmd.lower() == 'leave':
            await self._leave_room()
        elif cmd.lower() == 'chat':
            self.renderer.print_error("Usage: chat <message>")
        elif cmd.startswith('chat '):
            await self._send_chat(cmd[5:])
        else:
            self.renderer.print_error("In room: 'ready', 'leave', 'chat <msg>'")
    
    async def _handle_game_input(self, cmd: str) -> None:
        """Handle game commands."""
        cmd_lower = cmd.lower()
        
        if cmd_lower in ['pass', 'p']:
            await self._send_pass()
        elif cmd_lower in ['resign', 'r']:
            await self._send_resign()
        elif cmd_lower == 'save':
            await self._save_game()
        elif cmd_lower == 'help':
            self.renderer.print_help()
        elif cmd.startswith('chat '):
            await self._send_chat(cmd[5:])
        else:
            # Try to parse as move coordinates
            await self._parse_and_send_move(cmd)
    
    async def _parse_and_send_move(self, coord: str) -> None:
        """Parse coordinate and send move."""
        try:
            coord = coord.strip().lower()
            if len(coord) < 2:
                self.renderer.print_error("Invalid coordinate format")
                return
            
            # Parse letter + number (e.g., "d4", "q16")
            col_char = coord[0]
            row_str = coord[1:]
            
            x = ord(col_char) - ord('a')
            y = int(row_str) - 1
            
            # Convert to 0-indexed from bottom
            y = self.game_data.board_size - y - 1
            
            if not self.game_data.is_my_turn():
                self.renderer.print_error("Not your turn!")
                return
            
            move_msg = Messages.make_move(x, y, self.game_data.my_color)
            await self.websocket.send(MessageBuilder.serialize(move_msg))
            
        except (ValueError, IndexError):
            self.renderer.print_error(f"Invalid coordinate: {coord}")
    
    # ========================================================================
    # SERVER MESSAGE HANDLERS
    # ========================================================================
    
    async def _handle_connected(self, message: Dict) -> None:
        """Handle successful connection."""
        self.player_id = message.get("player_id")
        self.username = message.get("username", self.username)
        self.state = ClientState.LOBBY
        
        self.renderer.clear()
        self.renderer.print_header(f"OS-GO Network Client - {self.username}")
        self.renderer.print_system_message(f"Connected as {self.username} ({self.player_id})")
        self.renderer.print_lobby_menu()
    
    async def _handle_room_created(self, message: Dict) -> None:
        """Handle room creation confirmation."""
        room_data = message.get("room", {})
        self.current_room = room_data
        self.game_data.my_color = message.get("your_color")
        self.state = ClientState.IN_ROOM
        
        self.renderer.clear()
        self.renderer.print_header("Room Created")
        self.renderer.print_room_info(room_data)
        self.renderer.print_system_message(f"Your color: {self.game_data.my_color}")
        self.renderer.print_system_message("Type 'ready' when prepared, 'leave' to exit")
    
    async def _handle_room_joined(self, message: Dict) -> None:
        """Handle room join confirmation."""
        room_data = message.get("room", {})
        self.current_room = room_data
        self.game_data.my_color = message.get("your_color")
        self.state = ClientState.IN_ROOM
        
        self.renderer.clear()
        self.renderer.print_header("Joined Room")
        self.renderer.print_room_info(room_data)
        self.renderer.print_system_message(f"Your color: {self.game_data.my_color}")
        self.renderer.print_system_message("Type 'ready' when prepared, 'leave' to exit")
    
    async def _handle_room_left(self, message: Dict) -> None:
        """Handle room leave confirmation."""
        self.current_room = None
        self.game_data = GameData()
        self.state = ClientState.LOBBY
        
        self.renderer.clear()
        self.renderer.print_header("OS-GO Network Lobby")
        self.renderer.print_system_message("Left room")
        self.renderer.print_lobby_menu()
    
    async def _handle_room_list(self, message: Dict) -> None:
        """Handle room list update."""
        self.available_rooms = message.get("rooms", [])
        
        self.renderer.print_header("Available Rooms")
        if not self.available_rooms:
            self.renderer.print_system_message("No rooms available. Create one!")
        else:
            for room in self.available_rooms:
                players = len(room.get('players', []))
                print(f"  {room.get('id')} - {room.get('name')} ({players}/2)")
    
    async def _handle_room_update(self, message: Dict) -> None:
        """Handle room state update."""
        update_type = message.get("message", "Room updated")
        self.renderer.print_system_message(update_type)
    
    async def _handle_player_joined(self, message: Dict) -> None:
        """Handle another player joining."""
        player = message.get("player", {})
        self.renderer.print_system_message(
            f"Player joined: {player.get('username', 'Unknown')} ({player.get('color', '?')})"
        )
        
        # Update room data
        if self.current_room:
            if 'players' not in self.current_room:
                self.current_room['players'] = []
            self.current_room['players'].append(player)
    
    async def _handle_player_left(self, message: Dict) -> None:
        """Handle player leaving."""
        player_id = message.get("player_id", "unknown")
        self.renderer.print_system_message(f"Player left: {player_id}")
    
    async def _handle_game_start(self, message: Dict) -> None:
        """Handle game start."""
        game_state = message.get("game_state", {})
        settings = message.get("settings", {})
        
        self.game_data.board_size = settings.get("board_size", 19)
        self.game_data.moves = game_state.get("moves", [])
        self.game_data.current_turn = game_state.get("current_turn", "black")
        self.state = ClientState.PLAYING
        
        self.renderer.clear()
        self.renderer.print_header("Game Started!")
        self.renderer.print_board(self.game_data.board_size, self.game_data.moves, self.game_data.my_color)
        self.renderer.print_game_status(self.game_data, self.current_room)
        self.renderer.print_help()
    
    async def _handle_move_made(self, message: Dict) -> None:
        """Handle move confirmation from server."""
        move_type = message.get("move_type", "move")
        
        if move_type == "pass":
            color = message.get("color", "unknown")
            self.game_data.current_turn = "white" if color == "black" else "black"
            self.renderer.print_system_message(f"{color} passed")
        else:
            x, y = message.get("x"), message.get("y")
            color = message.get("color", "unknown")
            move_number = message.get("move_number", 0)
            
            self.game_data.moves.append({"x": x, "y": y, "color": color})
            self.game_data.current_turn = "white" if color == "black" else "black"
            
            # Convert to human-readable
            col = chr(ord('A') + x)
            row = self.game_data.board_size - y
            
            self.renderer.clear()
            self.renderer.print_header(f"Move {move_number}: {color} at {col}{row}")
            self.renderer.print_board(self.game_data.board_size, self.game_data.moves, self.game_data.my_color)
            self.renderer.print_game_status(self.game_data, self.current_room)
    
    async def _handle_invalid_move(self, message: Dict) -> None:
        """Handle invalid move error."""
        desc = message.get("description", "Invalid move")
        self.renderer.print_error(desc)
    
    async def _handle_game_over(self, message: Dict) -> None:
        """Handle game end."""
        winner = message.get("winner")
        reason = message.get("reason", "unknown")
        score_b = message.get("score_black")
        score_w = message.get("score_white")
        
        self.state = ClientState.FINISHED
        
        self.renderer.print_header("GAME OVER")
        if winner:
            self.renderer.print_system_message(f"Winner: {winner}!")
        else:
            self.renderer.print_system_message("Game ended in draw")
        
        self.renderer.print_system_message(f"Reason: {reason}")
        if score_b is not None and score_w is not None:
            self.renderer.print_system_message(f"Score - Black: {score_b}, White: {score_w}")
        
        self.renderer.print_system_message("Type 'save' to save SGF, 'q' to quit")
    
    async def _handle_sync_state(self, message: Dict) -> None:
        """Handle state synchronization."""
        room_data = message.get("room")
        game_state = message.get("game_state")
        
        if room_data:
            self.current_room = room_data
        if game_state:
            self.game_data.moves = game_state.get("moves", [])
            self.game_data.current_turn = game_state.get("current_turn", "black")
            self.renderer.print_system_message("State synchronized")
    
    async def _handle_chat(self, message: Dict) -> None:
        """Handle chat message."""
        username = message.get("player", "Unknown")
        text = message.get("text", "")
        self.renderer.print_chat_message(username, text)
    
    async def _handle_error(self, message: Dict) -> None:
        """Handle server error."""
        code = message.get("code", "UNKNOWN")
        desc = message.get("description", "Unknown error")
        self.renderer.print_error(f"[{code}] {desc}")
    
    async def _handle_ping(self, message: Dict) -> None:
        """Handle server ping."""
        await self.websocket.send(MessageBuilder.serialize(
            Messages.create(MessageType.PONG)
        ))
    
    # ========================================================================
    # CLIENT ACTIONS
    # ========================================================================
    
    async def _create_room_interactive(self) -> None:
        """Interactive room creation."""
        loop = asyncio.get_event_loop()
        
        print("\n--- Create Room ---")
        name = await loop.run_in_executor(None, input, "Room name: ")
        
        print("\nBoard size: 1) 9x9  2) 13x13  3) 19x19")
        size_choice = await loop.run_in_executor(None, input, "Choice (3): ")
        size_map = {"1": 9, "2": 13, "3": 19}
        board_size = size_map.get(size_choice.strip(), 19)
        
        print("\nRules: 1) Chinese  2) Japanese")
        rules_choice = await loop.run_in_executor(None, input, "Choice (1): ")
        rules = "japanese" if rules_choice.strip() == "2" else "chinese"
        
        komi = 7.5 if rules == "chinese" else 6.5
        
        settings = GameSettings(
            board_size=board_size,
            rules=rules,
            komi=komi,
        )
        
        password = await loop.run_in_executor(None, input, "Password (empty for public): ")
        password = password.strip() or None
        
        msg = Messages.create_room(name or f"{self.username}'s Room", settings, password)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _join_room_interactive(self) -> None:
        """Interactive room joining."""
        loop = asyncio.get_event_loop()
        
        print("\n--- Join Room ---")
        room_id = await loop.run_in_executor(None, input, "Room ID: ")
        password = await loop.run_in_executor(None, input, "Password (if any): ")
        password = password.strip() or None
        
        msg = Messages.join_room(room_id.strip(), password)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _list_rooms(self) -> None:
        """Request room list from server."""
        # Server pushes room list automatically, but we can request it
        self.renderer.print_system_message("Fetching room list...")
        # In full implementation, add a request message type
    
    async def _send_ready(self) -> None:
        """Send ready status."""
        msg = Messages.create(MessageType.READY)
        await self.websocket.send(MessageBuilder.serialize(msg))
        self.renderer.print_system_message("You are ready! Waiting for opponent...")
    
    async def _leave_room(self) -> None:
        """Leave current room."""
        msg = Messages.create(MessageType.LEAVE_ROOM)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _send_move(self, x: int, y: int) -> None:
        """Send move to server."""
        msg = Messages.make_move(x, y, self.game_data.my_color)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _send_pass(self) -> None:
        """Send pass move."""
        msg = Messages.create(MessageType.PASS)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _send_resign(self) -> None:
        """Send resignation."""
        msg = Messages.create(MessageType.RESIGN)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _send_chat(self, text: str) -> None:
        """Send chat message."""
        msg = Messages.chat(text)
        await self.websocket.send(MessageBuilder.serialize(msg))
    
    async def _save_game(self) -> None:
        """Save game to SGF file."""
        if not self.game_data.moves:
            self.renderer.print_error("No moves to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_{timestamp}.sgf"
        
        # Basic SGF generation
        sgf = self._generate_sgf()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(sgf)
            self.renderer.print_system_message(f"Game saved to {filename}")
        except IOError as e:
            self.renderer.print_error(f"Failed to save: {e}")
    
    def _generate_sgf(self) -> str:
        """Generate SGF format from game data."""
        size = self.game_data.board_size
        sgf = f"(;GM[1]FF[4]SZ[{size}]"
        
        # Add game info
        if self.current_room:
            settings = self.current_room.get('settings', {})
            sgf += f"KM[{settings.get('komi', 7.5)}]"
            sgf += f"RU[{settings.get('rules', 'chinese')}]"
        
        # Add moves
        for move in self.game_data.moves:
            if move.get('type') == 'pass':
                color = 'B' if move['color'] == 'black' else 'W'
                sgf += f";{color}[]"
            else:
                color = 'B' if move['color'] == 'black' else 'W'
                x = move['x']
                y = move['y']
                # SGF uses letters a-s
                x_char = chr(ord('a') + x)
                y_char = chr(ord('a') + y)
                sgf += f";{color}[{x_char}{y_char}]"
        
        sgf += ")"
        return sgf


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Parse arguments and start client."""
    parser = argparse.ArgumentParser(description='OS-GO Network PvP Client')
    parser.add_argument('server', nargs='?', default='ws://localhost:8765/ws',
                       help='WebSocket server URL')
    parser.add_argument('-u', '--username', default='',
                       help='Player username')
    parser.add_argument('--no-reconnect', action='store_true',
                       help='Disable auto-reconnect')
    
    args = parser.parse_args()
    
    config = ClientConfig(
        server_url=args.server,
        username=args.username,
        auto_reconnect=not args.no_reconnect,
    )
    
    client = NetworkClient(config)
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
