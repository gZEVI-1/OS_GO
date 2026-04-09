import subprocess

import os
from typing import Optional, Dict
from core_adapter import *


class GNUGoBot:
    """Обёртка для взаимодействия с GNUGo через GTP протокол"""
    
    def __init__(self, gnugo_path: str, board_size: int = 19, komi: float = 6.5):
        self.gnugo_path = gnugo_path
        self.board_size = board_size
        self.komi = komi
        self.process: Optional[subprocess.Popen] = None
    
    def start(self) -> bool:
        """Запускает GNU Go """
        if not os.path.exists(self.gnugo_path):
            return False
        
        try:
            self.process = subprocess.Popen(
                [self.gnugo_path, "--mode", "gtp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            
            # Инициализация
            self._send_command(f"boardsize {self.board_size}")
            self._send_command("clear_board")
            self._send_command(f"komi {self.komi}")
            
            return True
            
        except Exception:
            return False
    
    def stop(self):
        """Останавливает GNU Go"""
        if self.process:
            try:
                self._send_command("quit")
            except:
                pass
            self.process.terminate()
            self.process = None
    
    def _send_command(self, cmd: str) -> str:
        """Отправляет команду GTP и возвращает ответ"""
        if not self.process:
            raise RuntimeError("GNU Go не запущен")
        
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        
        lines = []
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            line = line.rstrip("\n")
            lines.append(line)
            if line == "":
                break
        
        return "\n".join(lines)
    
    def play_move(self, color: str, x: int, y: int, is_pass: bool = False) -> bool:
        """
        Отправляет ход в GNU Go
        color: 'B' или 'W'
        """
        if is_pass:
            cmd = f"play {color} pass"
        else:
            letter = CoordinateUtils.index_to_letter(x) # type: ignore
            gtp_y = y + 1
            cmd = f"play {color} {letter}{gtp_y}"
        
        response = self._send_command(cmd)
        return not response.startswith('?')
    
    def get_move(self, color: str) -> Optional[Dict]:
        """
        Получает ход от GNU Go
        Returns: {'is_pass': bool, 'x': int, 'y': int} или None при ошибке
        """
        response = self._send_command(f"genmove {color}")
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('='):
                move_str = line[1:].strip()
                
                if move_str == 'pass':
                    return {'is_pass': True, 'x': -1, 'y': -1}
                
                if move_str and len(move_str) >= 2:
                    try:
                        letter = move_str[0]
                        y = int(move_str[1:]) - 1
                        x = CoordinateUtils.letter_to_index(letter) # type: ignore
                        return {'is_pass': False, 'x': x, 'y': y}
                    except:
                        pass
        
        return None
    
    def is_alive(self) -> bool:
        """Проверяет, работает ли GNU Go"""
        return self.process is not None
