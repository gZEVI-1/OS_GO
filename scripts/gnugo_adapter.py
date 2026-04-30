import subprocess
import os
import sys
from typing import Optional, Dict


class GNUGoBot:
    def __init__(self, gnugo_path: str, board_size: int = 19, komi: float = 6.5):
        self.gnugo_path = gnugo_path
        self.board_size = board_size
        self.komi = komi
        self.process: Optional[subprocess.Popen] = None
        self._started = False
    
    def start(self) -> bool:
        """Запускает GNU Go"""
        print(f"[GNUGoBot] Проверка пути: {self.gnugo_path}")
        
        if not os.path.exists(self.gnugo_path):
            print(f"[GNUGoBot] ❌ Файл не существует: {self.gnugo_path}")
            return False
        
        try:
            # Windows-specific flags
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
            
            print(f"[GNUGoBot] Запуск процесса...")
            self.process = subprocess.Popen(
                [self.gnugo_path, "--mode", "gtp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )
            
            print(f"[GNUGoBot] Процесс создан: {self.process}")
            
            # Инициализация
            print(f"[GNUGoBot] Отправка boardsize {self.board_size}...")
            self._send_command(f"boardsize {self.board_size}")
            
            print(f"[GNUGoBot] Отправка clear_board...")
            self._send_command("clear_board")
            
            print(f"[GNUGoBot] Отправка komi {self.komi}...")
            self._send_command(f"komi {self.komi}")
            
            self._started = True
            print(f"[GNUGoBot] ✅ Успешно запущен")
            return True
            
        except Exception as e:
            print(f"[GNUGoBot] ❌ Ошибка запуска: {e}")
            import traceback
            traceback.print_exc()
            self.process = None
            return False
    
    def stop(self):
        """Останавливает GNU Go"""
        print(f"[GNUGoBot] Остановка, process={self.process}")
        if self.process:
            try:
                self._send_command("quit")
            except Exception as e:
                print(f"[GNUGoBot] Ошибка при quit: {e}")
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
        self._started = False
    
    def _send_command(self, cmd: str) -> str:
        """Отправляет команду GTP и возвращает ответ"""
        print(f"[GNUGoBot] _send_command: '{cmd}', process={self.process}")
        
        if self.process is None:
            raise RuntimeError("GNU Go не запущен (process is None)")
        
        if self.process.stdin is None:
            raise RuntimeError("GNU Go stdin is None (процесс мёртв?)")
        
        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            print(f"[GNUGoBot] Команда отправлена, читаем ответ...")
            
            lines = []
            while True:
                line = self.process.stdout.readline()
                if not line:
                    print(f"[GNUGoBot] ⚠️ stdout закрыт")
                    break
                line = line.rstrip("\n")
                lines.append(line)
                print(f"[GNUGoBot] Прочитано: '{line}'")
                if line == "":
                    break
            
            result = "\n".join(lines)
            print(f"[GNUGoBot] Полный ответ: {repr(result)}")
            return result
            
        except Exception as e:
            print(f"[GNUGoBot] ❌ Ошибка в _send_command: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def play_move(self, color: str, x: int, y: int, is_pass: bool = False) -> bool:
        """Отправляет ход в GNU Go"""
        print(f"[GNUGoBot] play_move: {color} at ({x},{y}) pass={is_pass}")
        
        if not self._started or self.process is None:
            print(f"[GNUGoBot] ❌ Бот не запущен!")
            return False
        
        if is_pass:
            cmd = f"play {color} pass"
        else:
            letter = self._index_to_letter(x)
            gtp_y = y + 1
            cmd = f"play {color} {letter}{gtp_y}"
        
        print(f"[GNUGoBot] Отправка: {cmd}")
        response = self._send_command(cmd)
        success = not response.startswith('?')
        print(f"[GNUGoBot] Результат: {'✅' if success else '❌'}")
        return success
    
    def get_move(self, color: str) -> Optional[Dict]:
        """Получает ход от GNU Go"""
        print(f"[GNUGoBot] get_move for {color}")
        
        if not self._started or self.process is None:
            print(f"[GNUGoBot] ❌ Бот не запущен!")
            return None
        
        try:
            response = self._send_command(f"genmove {color}")
            
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('='):
                    move_str = line[1:].strip()
                    print(f"[GNUGoBot] Получен ход: '{move_str}'")
                    
                    if move_str.lower() == 'pass':
                        return {'is_pass': True, 'x': -1, 'y': -1}
                    
                    if move_str and len(move_str) >= 2:
                        try:
                            letter = move_str[0].upper()
                            y = int(move_str[1:]) - 1
                            x = self._letter_to_index(letter)
                            print(f"[GNUGoBot] Распарсено: x={x}, y={y}")
                            return {'is_pass': False, 'x': x, 'y': y}
                        except Exception as e:
                            print(f"[GNUGoBot] Ошибка парсинга хода: {e}")
            
            print(f"[GNUGoBot] ❌ Не удалось распарсить ответ")
            return None
            
        except Exception as e:
            print(f"[GNUGoBot] ❌ Ошибка в get_move: {e}")
            return None
    
    def is_alive(self) -> bool:
        """Проверяет, работает ли GNU Go"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    @staticmethod
    def _index_to_letter(index: int) -> str:
        """A=0, B=1, ..., I пропускается"""
        if index < 8:
            return chr(65 + index)
        else:
            return chr(66 + index)  # Пропускаем I
    
    @staticmethod
    def _letter_to_index(letter: str) -> int:
        """Обратное преобразование"""
        letter = letter.upper()
        if letter == 'I':
            raise ValueError("Буква I не используется в координатах Го")
        if letter < 'I':
            return ord(letter) - ord('A')
        else:
            return ord(letter) - ord('A') - 1