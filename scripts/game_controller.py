"""
game_controller.py
==================
Абстракция над локальной (GameSession) и сетевой (NetworkClient) игрой.
Позволяет использовать один и тот же игровой цикл для всех режимов.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
import asyncio
from output_interface import GameDisplayState, get_output_interface, OutputType
from core_adapter import GameSession, PlayerType, CoordinateUtils


class GameController(ABC):
    """Единый интерфейс управления игрой"""

    @abstractmethod
    def get_display_state(self) -> Optional[GameDisplayState]: ...

    @abstractmethod
    def is_game_over(self) -> bool: ...

    @abstractmethod
    def is_my_turn(self) -> bool: ...

    @abstractmethod
    async def execute_command(self, cmd: str) -> Dict: ...
    # ^ возвращает dict с ключами: success, message, game_over, quit, undo

    @abstractmethod
    async def wait_for_turn(self) -> None: ...

    @abstractmethod
    def get_board_size(self) -> int: ...

    @abstractmethod
    def get_mode(self) -> str: ...

    @abstractmethod
    def get_game_result(self) -> Optional[tuple]: ...
    # ^ (winner, result_str) или None


class LocalController(GameController):
    """Обертка над локальной GameSession (PvP / PvE)"""

    def __init__(self, session: GameSession):
        self.session = session
        self.output = get_output_interface(OutputType.CONSOLE)

    def get_display_state(self) -> Optional[GameDisplayState]:
        from core_adapter import session_to_display_state
        mode = "pvp" if all(p['type'] == PlayerType.HUMAN 
                            for p in self.session.players.values()) else "pve"
        return session_to_display_state(self.session, mode=mode)

    def is_game_over(self) -> bool:
        return not self.session.game_active or self.session.game.is_game_over()

    def is_my_turn(self) -> bool:
        # В локальной игре всегда "наш" ход — игроки сидят за одним ПК
        return True

    async def execute_command(self, cmd: str) -> Dict:
        # make_human_move ожидает строку и сама парсит pass/undo/quit
        result = self.session.make_human_move(cmd)
        return result

    async def wait_for_turn(self) -> None:
        await asyncio.sleep(0)  # Не блокируемся, т.к. всегда наш ход

    def get_board_size(self) -> int:
        return self.session.board_size

    def get_mode(self) -> str:
        return "local"

    def get_game_result(self) -> Optional[tuple]:
        if not self.is_game_over():
            return None
        # Локальный результат можно расширить через GNU Go Analyzer при необходимости
        return ("Игра окончена", "Два паса или сдача")


class NetworkController(GameController):
    """Обертка над NetworkClient"""

    def __init__(self, client):
        self.client = client
        self.output = get_output_interface(OutputType.CONSOLE)
        self._game_ended = asyncio.Event()
        self._game_result: Optional[tuple] = None

        # Подписываемся на окончание игры
        def on_over(winner, result):
            self._game_result = (winner, result)
            self._game_ended.set()
            self.client._state_event.set()  # разбудить цикл

        self.client.on_game_over = on_over

    def get_display_state(self) -> Optional[GameDisplayState]:
        return self.client.get_display_state()

    def is_game_over(self) -> bool:
        from client import ConnectionState
        return (self._game_ended.is_set() or 
                self.client.state not in (ConnectionState.PLAYING, ConnectionState.IN_ROOM))

    def is_my_turn(self) -> bool:
        return self.client.is_my_turn()

    async def execute_command(self, cmd: str) -> Dict:
        lower = cmd.lower().split()

        if lower[0] == "pass":
            ok = await self.client.send_pass()
            if ok:
                await self.client.wait_for_state_change()
            return {"success": ok, "message": "Пас", "quit": False, "undo": False}

        if lower[0] == "undo":
            await self.client.request_undo()
            return {"success": True, "message": "Запрос на отмену отправлен", 
                    "quit": False, "undo": True}

        if lower[0] in ("resign", "quit"):
            if lower[0] == "resign":
                await self.client.send_resign()
            return {"success": True, "message": "Выход/сдача", "quit": True, "undo": False}

        if lower[0] == "chat":
            if len(lower) > 1:
                await self.client.send_chat(" ".join(lower[1:]))
            return {"success": True, "message": "Сообщение отправлено", 
                    "quit": False, "undo": False}

        parsed = CoordinateUtils.parse_move(cmd, self.client.board_size)
        if parsed and not parsed.get('quit') and not parsed.get('undo'):
            self.client._state_event.clear()
            ok = await self.client.send_move(parsed['x'], parsed['y'])
            if ok:
                await self.client.wait_for_state_change()
            return {"success": ok, "message": "Ход отправлен", 
                    "quit": False, "undo": False}

        return {"success": False, "message": "Неверная команда", 
                "quit": False, "undo": False}

    async def wait_for_turn(self) -> None:
        """Ждём, пока придёт наше время или игра не закончится"""
        while not self.is_my_turn() and not self.is_game_over():
            self.client._state_event.clear()
            try:
                await asyncio.wait_for(self.client._state_event.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

    def get_board_size(self) -> int:
        return self.client.board_size

    def get_mode(self) -> str:
        return "network"

    def get_game_result(self) -> Optional[tuple]:
        return self._game_result