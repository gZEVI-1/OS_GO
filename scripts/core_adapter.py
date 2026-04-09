
import go_engine as go
import os

from typing import Optional, Dict, List, Callable
from enum import Enum, auto
import config as cfg

from gnugo_adapter import  *


class PlayerType(Enum):
    """Тип игрока"""
    HUMAN = auto()
    GNU_GO = auto()


class CoordinateUtils:
    
    # Буква I пропускается в стандартной нотации Го
    SKIP_LETTER = 'I'
    SKIP_INDEX = 8  # Индекс буквы I 
    
    @staticmethod
    def index_to_letter(index: int) -> str:
        """Преобразует индекс в букву координаты (A-T без I)"""
        if index < CoordinateUtils.SKIP_INDEX:
            return chr(65 + index)
        else:
            return chr(66 + index)
    
    @staticmethod
    def letter_to_index(letter: str) -> int:
        """Преобразует букву координаты в индекс"""
        letter = letter.upper()
        if letter == CoordinateUtils.SKIP_LETTER:
            raise ValueError(f"Буква I не используется в координатах Го")
        
        if letter < CoordinateUtils.SKIP_LETTER:
            return ord(letter) - ord('A')
        else:
            return ord(letter) - ord('A') - 1
    
    @staticmethod
    def parse_move(move_str: str, board_size: int) -> Optional[Dict]:
        """
        Парсит строку хода 
        
        Returns:
            dict с ключами: is_pass, x, y, quit, undo
            или None если формат неверный
        """
        move_str = move_str.strip().lower()
        
        if move_str == 'pass':
            return {'is_pass': True, 'x': -1, 'y': -1, 'quit': False, 'undo': False}
        
        if move_str == 'quit':
            return {'is_pass': False, 'x': -1, 'y': -1, 'quit': True, 'undo': False}
        
        if move_str == 'undo':
            return {'is_pass': False, 'x': -1, 'y': -1, 'quit': False, 'undo': True}
        
        # Парсинг координат типа "a1"
        if len(move_str) < 2:
            return None
        
        try:
            letter = move_str[0].upper()
            y = int(move_str[1:]) - 1
            x = CoordinateUtils.letter_to_index(letter)
            
            if x < 0 or x >= board_size or y < 0 or y >= board_size:
                return None
            
            return {'is_pass': False, 'x': x, 'y': y, 'quit': False, 'undo': False}
            
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def format_move(x: int, y: int) -> str:
        """Форматирует координаты в строку (например, "a1")"""
        letter = CoordinateUtils.index_to_letter(x)
        return f"{letter}{y + 1}"



class GameSession:
    
    def __init__(self, board_size: int = 19, komi: float = 6.5):
        self.board_size = board_size
        self.komi = komi
        self.game: go.Game = go.Game(board_size)
        self.players: Dict[go.Color, Dict] = {
            go.Color.Black: {'name': 'Черные', 'type': PlayerType.HUMAN, 'gtp_color': 'B'},
            go.Color.White: {'name': 'Белые', 'type': PlayerType.HUMAN, 'gtp_color': 'W'}
        }
        self.gnugo_bot: Optional[GNUGoBot] = None # type: ignore
        self.game_active = False
        self.move_callbacks: List[Callable] = []
        self.game_over_callbacks: List[Callable] = []
        self.pass_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
    
    def set_player(self, color: go.Color, name: str, player_type: PlayerType, 
                   gnugo_path: Optional[str] = None):
        
        self.players[color] = {
            'name': name,
            'type': player_type,
            'gtp_color': 'B' if color == go.Color.Black else 'W',
            'gnugo_path': gnugo_path
        }
    
    def add_move_callback(self, callback: Callable):
        """Добавляет callback на совершение хода"""
        self.move_callbacks.append(callback)
    
    def add_game_over_callback(self, callback: Callable):
        """Добавляет callback на окончание игры"""
        self.game_over_callbacks.append(callback)
    
    def add_pass_callback(self, callback: Callable):
        """Добавляет callback на пас"""
        self.pass_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Добавляет callback на ошибку"""
        self.error_callbacks.append(callback)
    
    def start(self) -> bool:
        """Запускает игровую сессию"""
        # Проверяем, нужен ли GNU Go
        need_gnugo = any(p['type'] == PlayerType.GNU_GO for p in self.players.values())
        
        if need_gnugo:
            gnugo_path = self.players[go.Color.Black].get('gnugo_path') or \
                        self.players[go.Color.White].get('gnugo_path')
            
            if not gnugo_path or not os.path.exists(gnugo_path):
                self._notify_error("GNU Go не найден")
                return False
            
            self.gnugo_bot = GNUGoBot(gnugo_path, self.board_size, self.komi) # type: ignore
            if not self.gnugo_bot.start():
                self._notify_error("Не удалось запустить GNU Go")
                return False
        
        self.game_active = True
        
        # Если первый игрок бот, делаем его ход
        current = self.game.get_current_player()
        if self.players[current]['type'] == PlayerType.GNU_GO:
            self._make_bot_move()
        
        return True
    
    def stop(self):
        """Останавливает сессию"""
        self.game_active = False
        if self.gnugo_bot:
            self.gnugo_bot.stop()
            self.gnugo_bot = None
    
    def make_human_move(self, move_input: str) -> Dict:
        """
        Обрабатывает ход человека
        Returns: {'success': bool, 'message': str, 'game_over': bool, 'quit': bool, 'undo': bool}
        """
        if not self.game_active:
            return {'success': False,
                     'message': 'Игра не активна',
                       'game_over': False,
                         'quit': False,
                           'undo': False}
        
        current = self.game.get_current_player()
        if self.players[current]['type'] != PlayerType.HUMAN:
            return {'success': False,
                     'message': 'Сейчас не ваш ход',
                       'game_over': False,
                         'quit': False,
                           'undo': False}
        
        # Парсим ввод
        parsed = CoordinateUtils.parse_move(move_input, self.board_size)
        
        if parsed is None:
            return {'success': False,
                     'message': 'Неверный формат хода',
                       'game_over': False,
                         'quit': False,
                           'undo': False}
        
        if parsed.get('quit'):
            self.game_active = False
            return {'success': False,
                     'message': 'Выход из игры',
                       'game_over': False,
                         'quit': True,
                           'undo': False}
        
        if parsed.get('undo'):
            success = self.undo_move()
            return {
                'success': success,
                  'message': 'Ход отменен' if success else 'Нельзя отменить ход',
                    'game_over': False,
                      'quit': False,
                        'undo': True
            }
        
        # Выполняем ход
        try:
            success = self.game.make_move(parsed['x'], parsed['y'], parsed['is_pass'])
            
            if not success:
                return {'success': False,
                         'message': 'Недопустимый ход',
                           'game_over': False,
                             'quit': False,
                               'undo': False}
            
            # Синхронизируем с GNU Go если есть
            if self.gnugo_bot:
                gtp_color = self.players[current]['gtp_color']
                self.gnugo_bot.play_move(gtp_color, parsed['x'], parsed['y'], parsed['is_pass'])
            
            # Уведомляем о ходе
            move_info = {
                'x': parsed['x'],
                'y': parsed['y'],
                'is_pass': parsed['is_pass'],
                'color': current,
                'player_name': self.players[current]['name'],
                'move_number': self.game.get_move_number() - 1,
                'coord_str': CoordinateUtils.format_move(parsed['x'], parsed['y']) if not parsed['is_pass'] else 'pass'
            }
            self._notify_move(move_info)
            
            # Уведомляем о пасе
            if parsed['is_pass']:
                self._notify_pass(move_info)
            
            # Проверяем окончание игры
            if self.game.is_game_over():
                self._notify_game_over()
                return {'success': True,
                         'message': 'Игра окончена',
                           'game_over': True,
                             'quit': False,
                               'undo': False}
            
            # Ход бота если следующий игрок - бот
            next_player = self.game.get_current_player()
            if self.players[next_player]['type'] == PlayerType.GNU_GO:
                bot_result = self._make_bot_move()
                return {
                    'success': True,
                      'message': 'Ход выполнен',
                        'game_over': bot_result.get('game_over', False),
                          'quit': False,
                            'undo': False,
                              'bot_move': bot_result
                }
            
            return {'success': True,
                     'message': 'Ход выполнен',
                       'game_over': False,
                         'quit': False,
                           'undo': False}
            
        except Exception as e:
            self._notify_error(str(e))
            return {'success': False,
                     'message': f'Ошибка: {e}',
                       'game_over': False,
                         'quit': False,
                           'undo': False}
    
    def _make_bot_move(self) -> Dict:
        """Делает ход бота"""
        current = self.game.get_current_player()
        gtp_color = self.players[current]['gtp_color']
        
        move = self.gnugo_bot.get_move(gtp_color)
        
        if move is None:
            self._notify_error("GNU Go не вернул ход")
            return {'success': False, 'game_over': False}
        
        try:
            self.game.make_move(move['x'], move['y'], move['is_pass'])
            
            move_info = {
                'x': move['x'],
                'y': move['y'],
                'is_pass': move['is_pass'],
                'color': current,
                'player_name': self.players[current]['name'],
                'move_number': self.game.get_move_number() - 1,
                'coord_str': CoordinateUtils.format_move(move['x'], move['y']) if not move['is_pass'] else 'pass'
            }
            self._notify_move(move_info)
            
            if move['is_pass']:
                self._notify_pass(move_info)
            
            if self.game.is_game_over():
                self._notify_game_over()
                return {'success': True, 'game_over': True, 'move': move_info}
            
            return {'success': True, 'game_over': False, 'move': move_info}
            
        except Exception as e:
            self._notify_error(f"Ошибка хода бота: {e}")
            return {'success': False, 'game_over': False}
    
    def undo_move(self) -> bool:
        """Отменяет последний ход"""
        success = self.game.undo_last_move()
        if success and self.gnugo_bot:
            # Перезапускаем GNU Go для синхронизации
            self.gnugo_bot.stop()
            self.gnugo_bot.start()
            # Воспроизводим все ходы
            for move in self.game.sgf.get_moves():
                if not move.is_pass:
                    gtp_color = 'B' if move.color == go.Color.Black else 'W'
                    pos = move.pos
                    self.gnugo_bot.play_move(gtp_color, pos.x, pos.y, False)
                else:
                    gtp_color = 'B' if move.color == go.Color.Black else 'W'
                    self.gnugo_bot.play_move(gtp_color, -1, -1, True)
        return success
    
    def save_game(self, game_mode: str = "autosave") -> Optional[str]:
        """Сохраняет игру в SGF файл"""
        filepath = cfg.get_sgf_path(game_mode=game_mode)
        if self.game.save_game(filepath):
            return filepath
        return None
    
    def get_game_result(self, gnugo_analyzer=None) -> Optional[Dict]:
        """
        Получает результат игры через GNU Go анализатор
        """
        if gnugo_analyzer is None:
            return None
        
        try:
            sgf_content = self.game.get_sgf()
            result = gnugo_analyzer.analyze_sgf(sgf_content, self.board_size)
            return result
        except Exception:
            return None
    
    def get_current_state(self) -> Dict:
        """Возвращает текущее состояние игры"""
        current = self.game.get_current_player()
        return {
            'board': self.game.get_board(),
            'current_player': current,
            'current_player_name': self.players[current]['name'],
            'current_player_type': self.players[current]['type'],
            'move_number': self.game.get_move_number(),
            'passes': self.game.get_passes(),
            'game_over': self.game.is_game_over(),
            'board_size': self.board_size
        }
    
    def get_board_array(self) -> List[List[int]]:
        """Возвращает массив доски"""
        return self.game.get_board().get_board_array()
    
    def get_legal_moves(self) -> go.Board:
        """Возвращает доску с легальными ходами"""
        return self.game.get_legal_moves()
    
    def _notify_move(self, move_info: Dict):
        """Уведомляет о ходе"""
        for callback in self.move_callbacks:
            try:
                callback(move_info)
            except:
                pass
    
    def _notify_game_over(self):
        """Уведомляет об окончании игры"""
        for callback in self.game_over_callbacks:
            try:
                callback()
            except:
                pass
    
    def _notify_pass(self, move_info: Dict):
        """Уведомляет о пасе"""
        for callback in self.pass_callbacks:
            try:
                callback(move_info)
            except:
                pass
    
    def _notify_error(self, message: str):
        """Уведомляет об ошибке"""
        for callback in self.error_callbacks:
            try:
                callback(message)
            except:
                pass


def create_pvp_session(board_size: int, black_name: str, white_name: str) -> GameSession:
    """Фабрика для создания PvP сессии"""
    session = GameSession(board_size)
    session.set_player(go.Color.Black, black_name or "Игрок 1", PlayerType.HUMAN)
    session.set_player(go.Color.White, white_name or "Игрок 2", PlayerType.HUMAN)
    return session


def create_pve_session(board_size: int, player_color: go.Color, player_name: str,
                        gnugo_path: str, difficulty: Optional[str] = None) -> GameSession:
    """Фабрика для создания PvE сессии"""
    session = GameSession(board_size)
    
    if player_color == go.Color.Black:
        session.set_player(go.Color.Black, player_name or "Вы", PlayerType.HUMAN)
        session.set_player(go.Color.White, "GNU Go", PlayerType.GNU_GO, gnugo_path)
    else:
        session.set_player(go.Color.Black, "GNU Go", PlayerType.GNU_GO, gnugo_path)
        session.set_player(go.Color.White, player_name or "Вы", PlayerType.HUMAN)
    
    return session