
"""
OS-GO Output Interface — PySide6-Ready Edition
==============================================
Независимый интерфейс вывода для консоли, UI и сетевой игры.
Позволяет использовать один игровой код с разными фронтендами.

Для PySide6: наследуйте GameOutputInterface и реализуйте методы
с использованием Qt-виджетов. НЕ используйте блокирующий ввод.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class OutputType(Enum):
    CONSOLE = "console"
    UI = "ui"
    NETWORK = "network"


@dataclass
class GameDisplayState:
    """Состояние игры для отображения. Immutable-структура для GUI."""
    board_size: int
    board_array: List[List[int]]  # 0=пусто, 1=черный, 2=белый
    current_player: str  # "black" или "white"
    move_number: int
    passes: int
    last_move: Optional[Dict[str, Any]] = None
    captures: Dict[str, int] = None
    player_color: Optional[str] = None
    is_my_turn: bool = False
    mode: str = "pvp"  # pvp, pve, network

    def __post_init__(self):
        if self.captures is None:
            self.captures = {"black": 0, "white": 0}


@dataclass
class RoomDisplayState:
    """Состояние комнаты для отображения."""
    room_id: str
    players: List[Dict[str, Any]]
    my_color: Optional[str] = None
    status: str = "waiting"  # waiting, playing, finished


@dataclass
class MessageData:
    """Сообщение для отображения."""
    type: str  # info, error, success, warning
    text: str


class GameOutputInterface(ABC):
    """
    Базовый интерфейс для вывода игрового состояния.
    
    Примечание для PySide6:
    - Все show_* методы должны быть быстрыми и не блокировать event loop
    - get_input() в GUI должен возвращать пустую строку или вызывать
      callback; НЕ используйте блокирующий input()
    """

    @abstractmethod
    def clear_screen(self):
        """Очищает экран / сбрасывает UI."""
        pass

    @abstractmethod
    def show_game_state(self, state: GameDisplayState):
        """Отображает состояние игры (доска, захваты, ход)."""
        pass

    @abstractmethod
    def show_message(self, message: MessageData):
        """Показывает всплывающее/статусное сообщение."""
        pass

    @abstractmethod
    def show_board(self, board_array: List[List[int]], size: int,
                   last_move: Optional[Dict] = None):
        """Отображает только доску (без мета-информации)."""
        pass

    @abstractmethod
    def show_game_result(self, winner: str, result: str, reason: str):
        """Показывает результат игры (модальное окно / панель)."""
        pass

    @abstractmethod
    def show_room_state(self, state: RoomDisplayState):
        """Отображает состояние комнаты (игроки, готовность)."""
        pass

    @abstractmethod
    def show_room_list(self, rooms: List[Dict[str, Any]]):
        """Показывает список комнат (таблица / список)."""
        pass

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """
        Запрашивает ввод. В GUI должен быть НЕблокирующим
        (возвращает текущий текст или пустую строку).
        """
        pass

    @abstractmethod
    def show_help(self):
        """Показывает справку."""
        pass

    # --- Опциональные методы для GUI ---

    def show_prompt(self, prompt: str, callback: Optional[Callable[[str], None]] = None):
        """
        [GUI] Показывает диалог ввода с callback. 
        Не требуется для консоли, но обязателен для GUI-реализаций.
        """
        pass

    def show_chat_message(self, sender: str, text: str):
        """[GUI] Добавляет сообщение в чат."""
        pass

    def set_connection_status(self, status: str, details: str = ""):
        """[GUI] Обновляет индикатор подключения."""
        pass


class ConsoleOutput(GameOutputInterface):
    """Консольная реализация."""

    def __init__(self):
        self.use_colors = True

    def _get_stone_symbol(self, color: int, is_hoshi: bool = False) -> str:
        if color == 1:
            return "○"
        elif color == 2:
            return "●"
        else:
            return "+" if is_hoshi else "·"

    def _is_hoshi_point(self, x: int, y: int, size: int) -> bool:
        if size == 19:
            return (x in [3, 9, 15] and y in [3, 9, 15])
        elif size == 13:
            return (x in [3, 9] and y in [3, 9]) or (x == 6 and y == 6)
        elif size == 9:
            return (x in [2, 6] and y in [2, 6]) or (x == 4 and y == 4)
        return False

    def _index_to_letter(self, index: int) -> str:
        if index < 8:
            return chr(65 + index)
        else:
            return chr(66 + index)

    def clear_screen(self):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_board(self, board_array: List[List[int]], size: int,
                   last_move: Optional[Dict] = None):
        print("   ", end="")
        for i in range(size):
            letter = self._index_to_letter(i)
            print(f"{letter:2}", end="")
        print()
        for y in range(size):
            print(f"{y+1:2} ", end="")
            for x in range(size):
                val = board_array[y][x] if y < len(board_array) and x < len(board_array[y]) else 0
                is_hoshi = self._is_hoshi_point(x, y, size)
                symbol = self._get_stone_symbol(val, is_hoshi)
                print(f"{symbol} ", end="")
            print()

    def show_game_state(self, state: GameDisplayState):
        print("=" * 60)
        mode_str = state.mode.upper()
        print(f"           ИГРА ГО ({state.board_size}x{state.board_size}) — {mode_str}")
        print("=" * 60)
        print(f"📊 Ход номер: {state.move_number}")
        turn_symbol = "○" if state.current_player == "black" else "●"
        if state.mode == "network" and state.player_color:
            my_color_symbol = "○" if state.player_color == "black" else "●"
            print(f"🎮 Вы играете: {my_color_symbol} ({state.player_color})")
            print(f"🔄 Ход: {turn_symbol} {'(ВАШ!)' if state.is_my_turn else '(противник)'}")
        else:
            print(f"🎮 Текущий игрок: {turn_symbol} {state.current_player}")
        print(f"⏭️ Пасов подряд: {state.passes}")
        print(f"⚫ Черные взяли: {state.captures.get('black', 0)}")
        print(f"⚪ Белые взяли: {state.captures.get('white', 0)}")
        if state.last_move:
            if state.last_move.get("is_pass"):
                print("➡️ Последний ход: PASS")
            else:
                x = state.last_move["x"]
                y = state.last_move["y"]
                coord = self._index_to_letter(x) + str(y + 1)
                color = "○" if state.last_move.get("color") == "black" else "●"
                print(f"➡️ Последний ход: {coord} ({color})")
        else:
            print("➡️ Последний ход: —")
        print("-" * 60)
        self.show_board(state.board_array, state.board_size)

    def show_message(self, message: MessageData):
        icons = {"info": "ℹ️", "error": "❌", "success": "✅", "warning": "⚠️"}
        icon = icons.get(message.type, "•")
        print(f"\\n{icon} {message.text}\\n")

    def show_game_result(self, winner: str, result: str, reason: str):
        print("\\n" + "=" * 60)
        print("🏆 ИГРА ОКОНЧЕНА!")
        print("=" * 60)
        print(f"🥇 Победитель: {winner}")
        print(f"📊 Результат: {result}")
        print(f"📋 Причина: {reason}")
        print("=" * 60)

    def show_room_state(self, state: RoomDisplayState):
        print("=" * 60)
        print("           КОМНАТА")
        print("=" * 60)
        print(f"🆔 ID: {state.room_id}")
        if state.my_color:
            print(f"🎨 Ваш цвет: {'Черные' if state.my_color == 'black' else 'Белые'}")
        print("\\nИгроки:")
        for p in state.players:
            ready = "✅" if p.get("is_ready") else "⏳"
            print(f"  {ready} {p.get('name', 'Unknown')} ({p.get('color', '?')})")

    def show_room_list(self, rooms: List[Dict[str, Any]]):
        if not rooms:
            print("\\n📭 Нет доступных комнат")
            return
        print("\\n" + "=" * 60)
        print("           ДОСТУПНЫЕ КОМНАТЫ")
        print("=" * 60)
        print(f"{'ID':<10} {'Название':<20} {'Хост':<15} {'Размер':<8} {'Игроки':<10} {'Статус'}")
        print("-" * 60)
        for room in rooms:
            lock = "🔒" if room.get("has_password") else "  "
            name = room.get("name", "Unknown")[:18]
            host = room.get("host_name", "?")[:14]
            bs = room.get('board_size', 19)
            size = f"{bs}x{bs}"
            players = f"{room.get('player_count', 0)}/{room.get('max_players', 2)}"
            status = room.get("status", "waiting")
            print(f"{room.get('room_id', '????????'):<10} {lock}{name:<18} {host:<15} {size:<8} {players:<10} {status}")

    def get_input(self, prompt: str) -> str:
        try:
            return input(prompt).strip()
        except KeyboardInterrupt:
            return ""

    def show_help(self):
        print("""
        Справка:
        • D4, Q16 — координаты хода (без I)
        • pass — пропустить ход
        • undo — отменить ход
        • quit — выход
        • help — справка
        • chat <текст> — чат (сеть)
        • resign — сдаться (сеть)
        """)


# Глобальный экземпляр
_console_output = ConsoleOutput()


def get_output_interface(output_type: OutputType = OutputType.CONSOLE) -> GameOutputInterface:
    if output_type == OutputType.CONSOLE:
        return _console_output
    raise ValueError(f"Unsupported: {output_type}")


# Удобные функции

def clear_screen():
    _console_output.clear_screen()


def show_game_state(state: GameDisplayState):
    _console_output.show_game_state(state)


def show_message(msg_type: str, text: str):
    _console_output.show_message(MessageData(type=msg_type, text=text))


def show_board(board_array: List[List[int]], size: int, last_move: Optional[Dict] = None):
    _console_output.show_board(board_array, size, last_move)


def show_game_result(winner: str, result: str, reason: str):
    _console_output.show_game_result(winner, result, reason)


def show_room_state(state: RoomDisplayState):
    _console_output.show_room_state(state)


def show_room_list(rooms: List[Dict[str, Any]]):
    _console_output.show_room_list(rooms)


def get_input(prompt: str) -> str:
    return _console_output.get_input(prompt)


def show_help():
    _console_output.show_help()
