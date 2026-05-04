
"""
OS-GO Output Interface
======================
Независимый интерфейс вывода для консоли и UI.
Позволяет использовать один и тот же код игры с разными интерфейсами.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class OutputType(Enum):
    CONSOLE = "console"
    UI = "ui"
    NETWORK = "network"


@dataclass
class GameDisplayState:
    """Состояние игры для отображения"""
    board_size: int
    board_array: List[List[int]]  # 0=пусто, 1=черный, 2=белый
    current_player: str  # "black" или "white"
    move_number: int
    passes: int
    last_move: Optional[Dict[str, Any]] = None
    captures: Dict[str, int] = None
    player_color: Optional[str] = None  # Цвет игрока в сетевой игре
    is_my_turn: bool = False
    mode: str = "pvp"  # pvp, pve, network

    def __post_init__(self):
        if self.captures is None:
            self.captures = {"black": 0, "white": 0}


@dataclass
class RoomDisplayState:
    """Состояние комнаты для отображения"""
    room_id: str
    players: List[Dict[str, Any]]
    my_color: Optional[str] = None


@dataclass
class MessageData:
    """Сообщение для отображения"""
    type: str  # info, error, success, warning
    text: str


class GameOutputInterface(ABC):
    """Базовый интерфейс для вывода игрового состояния"""

    @abstractmethod
    def clear_screen(self):
        """Очищает экран"""
        pass

    @abstractmethod
    def show_game_state(self, state: GameDisplayState):
        """Отображает состояние игры"""
        pass

    @abstractmethod
    def show_message(self, message: MessageData):
        """Показывает сообщение"""
        pass

    @abstractmethod
    def show_board(self, board_array: List[List[int]], size: int,
                   last_move: Optional[Dict] = None):
        """Отображает доску"""
        pass

    @abstractmethod
    def show_game_result(self, winner: str, result: str, reason: str):
        """Показывает результат игры"""
        pass

    @abstractmethod
    def show_room_state(self, state: RoomDisplayState):
        """Отображает состояние комнаты"""
        pass

    @abstractmethod
    def show_room_list(self, rooms: List[Dict[str, Any]]):
        """Показывает список комнат"""
        pass

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """Запрашивает ввод у пользователя"""
        pass

    @abstractmethod
    def show_help(self):
        """Показывает справку"""
        pass


class ConsoleOutput(GameOutputInterface):
    """Консольная реализация интерфейса вывода"""

    def __init__(self):
        self.use_colors = True  # Можно отключить для простых терминалов

    def clear_screen(self):
        import os
        os.system('cls' if os.name == 'nt' else 'clear')

    def _get_stone_symbol(self, color: int, is_hoshi: bool = False) -> str:
        """Возвращает символ для камня"""
        if color == 1:  # Black
            return "○"
        elif color == 2:  # White
            return "●"
        else:
            return "+" if is_hoshi else "·"

    def _is_hoshi_point(self, x: int, y: int, size: int) -> bool:
        """Проверяет точку хоси"""
        if size == 19:
            return (x in [3, 9, 15] and y in [3, 9, 15])
        elif size == 13:
            return (x in [3, 9] and y in [3, 9]) or (x == 6 and y == 6)
        elif size == 9:
            return (x in [2, 6] and y in [2, 6]) or (x == 4 and y == 4)
        return False

    def _index_to_letter(self, index: int) -> str:
        """Преобразует индекс в букву (без I)"""
        if index < 8:
            return chr(65 + index)
        else:
            return chr(66 + index)

    def show_board(self, board_array: List[List[int]], size: int,
                   last_move: Optional[Dict] = None):
        """Отображает доску в компактном формате (как console_back.py)"""
        # Заголовок
        print("   ", end="")
        for i in range(size):
            letter = self._index_to_letter(i)
            print(f"{letter:2}", end="")
        print()

        # Доска
        for y in range(size):
            print(f"{y+1:2} ", end="")
            for x in range(size):
                val = board_array[y][x] if y < len(board_array) and x < len(board_array[y]) else 0
                is_hoshi = self._is_hoshi_point(x, y, size)
                symbol = self._get_stone_symbol(val, is_hoshi)
                print(f"{symbol} ", end="")
            print()

    def show_game_state(self, state: GameDisplayState):
        """Отображает состояние игры"""
        print("=" * 60)
        mode_str = state.mode.upper()
        print(f"           ИГРА ГО ({state.board_size}x{state.board_size}) — {mode_str}")
        print("=" * 60)
        print(f"📊 Ход номер: {state.move_number}")

        turn_symbol = "○" if state.current_player == "black" else "●"
        is_my_turn = state.is_my_turn

        if state.mode == "network" and state.player_color:
            my_color_symbol = "○" if state.player_color == "black" else "●"
            print(f"🎮 Вы играете: {my_color_symbol} ({state.player_color})")
            print(f"🔄 Ход: {turn_symbol} {'(ВАШ!)' if is_my_turn else '(противник)'}")
        else:
            print(f"🎮 Текущий игрок: {turn_symbol} {state.current_player}")

        print(f"⏭️ Пасов подряд: {state.passes}")
        print(f"⚫ Черные взяли: {state.captures.get('black', 0)}")
        print(f"⚪ Белые взяли: {state.captures.get('white', 0)}")

        # Последний ход — текстом, чтобы не ломать выравнивание доски
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
        """Показывает сообщение"""
        icons = {
            "info": "ℹ️",
            "error": "❌",
            "success": "✅",
            "warning": "⚠️"
        }
        icon = icons.get(message.type, "•")
        print(f"\n{icon} {message.text}\n")

    def show_game_result(self, winner: str, result: str, reason: str):
        """Показывает результат игры"""
        print("\n" + "=" * 60)
        print("🏆 ИГРА ОКОНЧЕНА!")
        print("=" * 60)
        print(f"🥇 Победитель: {winner}")
        print(f"📊 Результат: {result}")
        print(f"📋 Причина: {reason}")
        print("=" * 60)

    def show_room_state(self, state: RoomDisplayState):
        """Отображает состояние комнаты"""
        print("=" * 60)
        print("           КОМНАТА")
        print("=" * 60)
        print(f"🆔 ID комнаты: {state.room_id}")
        if state.my_color:
            color_name = "Черные" if state.my_color == "black" else "Белые"
            print(f"🎨 Ваш цвет: {color_name}")
        print("\nИгроки в комнате:")
        for p in state.players:
            ready = "✅" if p.get("is_ready") else "⏳"
            color = p.get("color", "?")
            name = p.get("name", "Unknown")
            print(f"  {ready} {name} ({color})")

    def show_room_list(self, rooms: List[Dict[str, Any]]):
        """Показывает список комнат"""
        if not rooms:
            print("\n📭 Нет доступных комнат")
            return

        print("\n" + "=" * 60)
        print("           ДОСТУПНЫЕ КОМНАТЫ")
        print("=" * 60)
        print(f"{'ID':<10} {'Название':<20} {'Хост':<15} {'Размер':<8} {'Игроки':<10} {'Статус'}")
        print("-" * 60)

        for room in rooms:
            lock = "🔒" if room.get("has_password") else "  "
            name = room.get("name", "Unknown")[:18]
            host = room.get("host_name", "?")[:14]
            board_size = room.get('board_size', 19)
            size = f"{board_size}x{board_size}"
            players = f"{room.get('player_count', 0)}/{room.get('max_players', 2)}"
            status = room.get("status", "waiting")
            print(f"{room.get('room_id', '????????'):<10} {lock}{name:<18} {host:<15} {size:<8} {players:<10} {status}")

    def get_input(self, prompt: str) -> str:
        """Запрашивает ввод"""
        try:
            return input(prompt).strip()
        except KeyboardInterrupt:
            return ""

    def show_help(self):
        """Показывает справку"""
        print("""
Справка по командам:

  • D4, Q16 и т.д. — координаты хода (буква + число)
  • pass — пропустить ход
  • undo — отменить последний ход
  • quit — выход из игры
  • help — показать эту справку
  • chat <текст> — отправить сообщение в чате (сетевая игра)
  • resign — сдаться (сетевая игра)

  Буква 'I' не используется в координатах!
""")


# Глобальный экземпляр для использования в коде
_console_output = ConsoleOutput()


def get_output_interface(output_type: OutputType = OutputType.CONSOLE) -> GameOutputInterface:
    """Фабрика для получения интерфейса вывода"""
    if output_type == OutputType.CONSOLE:
        return _console_output
    # В будущем можно добавить UI и другие интерфейсы
    raise ValueError(f"Unsupported output type: {output_type}")


# Удобные функции для прямого использования
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