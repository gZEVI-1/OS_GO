# sgf_loader.py

import re
import go_engine as go
import config as cfg
from pathlib import Path
from typing import List, Tuple, Optional

class SGFLoader:
    """Загрузчик SGF файлов"""
    
    @staticmethod
    def load_from_file(filename: str, game: go.Game) -> bool:
        """Загружает партию из SGF файла в существующий Game объект"""
        try:
            filepath = Path(filename)
            if not filepath.exists():
                possible_path = cfg.GAMES_DIR / filename
                if possible_path.exists():
                    filepath = possible_path
                else:
                    print(f"❌ Файл не найден: {filename}")
                    return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                sgf_content = f.read()
            return SGFLoader.load_from_string(sgf_content, game)
        except Exception as e:
            print(f"❌ Ошибка загрузки SGF: {e}")
            return False
    
    @staticmethod
    def load_from_string(sgf_content: str, game: go.Game) -> bool:
        """Загружает партию из строки SGF в Game объект"""
        moves = SGFLoader.parse_moves(sgf_content)
        
        for move in moves:
            if move['is_pass']:
                game.make_move(-1, -1, True)
            else:
                game.make_move(move['x'], move['y'], False)
        
        return True
    
    @staticmethod
    def parse_moves(sgf_content: str) -> List[dict]:
        """Парсит ходы из SGF строки"""
        moves = []
        
        #регулярка для поиска ходов: ;B[dd] или ;W[] (пас)
        pattern = r';([BW])\[([a-z]{0,2})\]'
        
        for match in re.finditer(pattern, sgf_content):
            color = match.group(1)
            coord = match.group(2)
            
            move = {
                'color': go.Color.Black if color == 'B' else go.Color.White,
                'is_pass': len(coord) == 0,
                'x': -1,
                'y': -1
            }
            
            if coord and len(coord) >= 2:
                x = ord(coord[0]) - ord('a')
                if x >= 8:  #пропускаем 'i'
                    x -= 1
                y = ord(coord[1]) - ord('a')
                if y >= 8:
                    y -= 1
                move['x'] = x
                move['y'] = y
            
            moves.append(move)
        
        return moves
    
    @staticmethod
    def get_board_size(sgf_content: str) -> int:
        """Получает размер доски из SGF"""
        match = re.search(r'SZ\[(\d+)\]', sgf_content)
        if match:
            return int(match.group(1))
        return 19
    
    @staticmethod
    def get_player_names(sgf_content: str) -> Tuple[str, str]:
        """Получает имена игроков из SGF"""
        black = re.search(r'PB\[([^\]]*)\]', sgf_content)
        white = re.search(r'PW\[([^\]]*)\]', sgf_content)
        return (
            black.group(1) if black else "Черные",
            white.group(1) if white else "Белые"
        )
    
    @staticmethod
    def get_result(sgf_content: str) -> Optional[str]:
        """Получает результат из SGF"""
        match = re.search(r'RE\[([^\]]*)\]', sgf_content)
        return match.group(1) if match else None
    
    @staticmethod
    def get_komi(sgf_content: str) -> float:
        """Получает коми из SGF"""
        match = re.search(r'KM\[([\d\.]+)\]', sgf_content)
        if match:
            return float(match.group(1))
        return 6.5