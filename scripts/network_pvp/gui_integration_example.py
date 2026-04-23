"""
OS-GO PySide6 GUI Integration Example
======================================

Example of integrating NetworkPvPGame with PySide6 GUI.
This shows the callback-based architecture for frontend binding.

Usage:
    This is a reference implementation, not a complete GUI.
    Copy relevant parts into your interface/windows modules.
"""

from PySide6.QtCore import QObject, Signal, Slot, QThread
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
import asyncio
import sys

# Import network module
from console_pvp_network import NetworkPvPGame, NetworkGameCallbacks, NetworkGamePhase


class NetworkGameWorker(QThread):
    """Background thread for async network operations."""
    
    connected = Signal()
    disconnected = Signal()
    roomJoined = Signal(dict)
    gameStarted = Signal(dict)
    moveMade = Signal(dict)
    gameOver = Signal(dict)
    chatReceived = Signal(str, str)  # username, text
    error = Signal(str)
    opponentJoined = Signal(dict)
    opponentLeft = Signal()
    turnChanged = Signal(str)  # current turn color
    stateSynced = Signal(dict)
    
    def __init__(self, server_url: str, username: str):
        super().__init__()
        self.server_url = server_url
        self.username = username
        self.game: NetworkPvPGame = None
        self._running = False
    
    def run(self):
        """Run async event loop in thread."""
        self._running = True
        asyncio.run(self._main_loop())
    
    async def _main_loop(self):
        """Initialize and run network game."""
        # Create game with callbacks wired to Qt signals
        self.game = NetworkPvPGame(
            server_url=self.server_url,
            username=self.username,
            callbacks=NetworkGameCallbacks(
                on_connect=self.connected.emit,
                on_disconnect=self.disconnected.emit,
                on_room_joined=self.roomJoined.emit,
                on_game_started=self.gameStarted.emit,
                on_move_made=self.moveMade.emit,
                on_game_over=self.gameOver.emit,
                on_chat=self.chatReceived.emit,
                on_error=self.error.emit,
                on_opponent_joined=self.opponentJoined.emit,
                on_opponent_left=self.opponentLeft.emit,
                on_turn_change=self.turnChanged.emit,
                on_state_sync=self.stateSynced.emit,
            )
        )
        
        # Connect to server
        if await self.game.initialize():
            await self.game.run()
    
    async def create_room(self, name: str, board_size: int = 19, 
                         rules: str = "chinese"):
        """Create a game room."""
        from protocol import GameSettings
        settings = GameSettings(board_size=board_size, rules=rules)
        await self.game.create_room(name, settings)
    
    async def join_room(self, room_id: str):
        """Join existing room."""
        await self.game.join_room(room_id)
    
    async def make_move(self, x: int, y: int):
        """Send move to server."""
        await self.game.make_move(x, y)
    
    async def pass_turn(self):
        """Pass turn."""
        await self.game.pass_turn()
    
    async def resign(self):
        """Resign game."""
        await self.game.resign()
    
    async def send_chat(self, text: str):
        """Send chat."""
        await self.game.send_chat(text)
    
    async def set_ready(self):
        """Signal ready."""
        await self.game.set_ready()
    
    def stop(self):
        """Stop the worker."""
        self._running = False
        asyncio.run(self.game.disconnect())
        self.quit()
        self.wait()


class NetworkPvPWindow(QMainWindow):
    """Example main window for network PvP."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS-GO Network PvP")
        self.resize(800, 600)
        
        self.worker = NetworkGameWorker(
            server_url="ws://localhost:8765/ws",
            username="GUI_Player"
        )
        
        # Connect signals to slots
        self.worker.connected.connect(self.on_connected)
        self.worker.gameStarted.connect(self.on_game_started)
        self.worker.moveMade.connect(self.on_move_made)
        self.worker.turnChanged.connect(self.on_turn_changed)
        self.worker.error.connect(self.on_error)
        
        self.worker.start()
    
    @Slot()
    def on_connected(self):
        """Handle connection."""
        QMessageBox.information(self, "Connected", "Connected to server!")
    
    @Slot(dict)
    def on_game_started(self, data):
        """Handle game start."""
        QMessageBox.information(self, "Game Started", "Game begins!")
    
    @Slot(dict)
    def on_move_made(self, move_data):
        """Handle move."""
        x = move_data.get("x")
        y = move_data.get("y")
        color = move_data.get("color")
        print(f"Move: {color} at ({x}, {y})")
        # Update board widget here
    
    @Slot(str)
    def on_turn_changed(self, turn):
        """Handle turn change."""
        print(f"Turn: {turn}")
        # Update UI indicators
    
    @Slot(str)
    def on_error(self, error_msg):
        """Handle error."""
        QMessageBox.critical(self, "Error", error_msg)
    
    def closeEvent(self, event):
        """Clean shutdown."""
        self.worker.stop()
        event.accept()


def main():
    """Run GUI example."""
    app = QApplication(sys.argv)
    window = NetworkPvPWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
