
import re
import subprocess
import os
import tempfile
gnugo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot", "gnugo-3.8", "gnugo.exe")

class GnuGoAnalyzer:
    def __init__(self, gnugo_path):
        """
        Инициализация анализатора GNU Go
        :param gnugo_path: путь к исполняемому файлу GNU Go
        """
        self.gnugo_path = gnugo_path
        self.temp_dir = os.path.join(tempfile.gettempdir(), f"TEMP_gnugo_analysis")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    
    def analyze_sgf(self, sgf_content, board_size=19):
        """
        Анализирует SGF файл с помощью GNU Go и возвращает результат подсчета очков
        """
        try:
            #SGF во временный файл
            sgf_file = os.path.join(self.temp_dir, "game.sgf")
            with open(sgf_file, 'w', encoding='utf-8') as f:
                f.write(sgf_content)
            
            #командный файл
            cmd_file = os.path.join(self.temp_dir, "commands.txt")
            with open(cmd_file, 'w') as f:
                f.write(f"loadsgf {sgf_file}\n")
                f.write("final_score\n")
                f.write("quit\n")
            
            #в консоль команды из файла
            cmd = f'type "{cmd_file}" | "{self.gnugo_path}" --mode gtp --boardsize {board_size} --chinese-rules --capture-all-dead --komi 6.5'
            
            # print(f"🔧 Выполняем команду: {cmd}")
            
            #запуск
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=None
            )
            
            # print(f"✅ Процесс завершен с кодом: {result.returncode}")
            # print(f"📄 Вывод GNU Go:\n{result.stdout}")
            
            #парсинг
            parsed_result = self._parse_gnugo_output(result.stdout)
            if parsed_result:
                return parsed_result
            
            return None
            
        except subprocess.TimeoutExpired:
            print("⏱️ Таймаут при анализе GNU Go")
            return None
        except Exception as e:
            print(f"❌ Ошибка при анализе GNU Go: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_gnugo_output(self, output):
        """
        Парсит вывод GNU Go
        """
        if not output:
            return None
        
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            if 'B+' in line or 'W+' in line:
                result_line = line.replace('=', '').strip()
                
                if '+' in result_line:
                    parts = result_line.split('+')
                    color = parts[0].strip()
                    points_str = parts[1].strip()
                    
                    points_match = re.search(r'(\d+\.?\d*)', points_str)
                    if points_match:
                        points = float(points_match.group(1))
                        
                        winner = "Черные" if color.upper() == 'B' else "Белые"
                        
                        return {
                            'winner': winner,
                            'winner_color': color.upper(),
                            'margin': points,
                            'full_result': f"{color}+{points}"
                        }
            
            elif '0' in line and ('=' in line or line.strip() == '0'):
                return {
                    'winner': "Ничья",
                    'winner_color': None,
                    'margin': 0,
                    'full_result': "0"
                }
        
        return None
    
    def get_detailed_scores(self, sgf_content, board_size=19):
        """
        Получает детальный подсчет очков с оценкой территории
        """
        try:
            #SGF во временный файл
            sgf_file = os.path.join(self.temp_dir, "game_detailed.sgf")
            with open(sgf_file, 'w', encoding='utf-8') as f:
                f.write(sgf_content)
            
            #командный файл
            cmd_file = os.path.join(self.temp_dir, "commands_detailed.txt")
            with open(cmd_file, 'w') as f:
                f.write(f"loadsgf {sgf_file}\n")
                f.write("estimate_score\n")
                f.write("final_score\n")
                f.write("quit\n")
            
            #команды в консоль
            cmd = f'type "{cmd_file}" | "{self.gnugo_path}" --mode gtp --boardsize {board_size} --chinese-rules --capture-all-dead --komi 6.5'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=None
            )
            
            #парсинг
            return self._parse_detailed_output(result.stdout)
            
        except Exception as e:
            print(f"❌ Ошибка при детальном анализе: {e}")
            return None
    
    def _parse_detailed_output(self, output):
        """
        Парсит детальный вывод с оценкой территории
        """
        if not output:
            return None
        
        lines = output.strip().split('\n')
        result = {}
        
        for line in lines:
            line = line.strip()
            
            if 'estimate_score' in line.lower() and '=' in line:
                continue
            elif '=' in line and ('black' in line.lower() or 'white' in line.lower()):
                estimate = line.replace('=', '').strip()
                result['estimate'] = estimate
            
            elif 'B+' in line or 'W+' in line:
                final = line.replace('=', '').strip()
                result['final'] = final
                
                if '+' in final:
                    color, points = final.split('+')
                    try:
                        points = float(points)
                        result['winner'] = 'Черные' if color.upper() == 'B' else 'Белые'
                        result['margin'] = points
                    except:
                        pass
        
        return result
    
    def cleanup(self):
        """Очищает временные файлы"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"🧹 Очищена временная папка: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Ошибка при очистке: {e}")


def check_gnugo_available(gnugo_path):
    """Проверяет доступность GNU Go"""
    try:
        result = subprocess.run(
            f'"{gnugo_path}" --version',
            shell=True,
            capture_output=True,
            text=True,
            timeout=100
        )
        return result.returncode == 0
    except:
        return False   

def get_winner(sgf_content: str, board_size: int = 19) -> int:

    """
    Определяет победителя через GNU Go.
    Возвращает: 1 (чёрные), 2 (белые), 0 (ничья), -1 (ошибка)
    """
    if not os.path.exists(gnugo_path):
        print(f"❌ GNU Go не найден: {gnugo_path}")
        return -1
    
    temp_dir = tempfile.mkdtemp()
    try:
        # SGF во временный файл
        sgf_file = os.path.join(temp_dir, "game.sgf")
        with open(sgf_file, 'w', encoding='utf-8') as f:
            f.write(sgf_content)
        
        # Команды для GNU Go
        cmd_file = os.path.join(temp_dir, "commands.txt")
        with open(cmd_file, 'w') as f:
            f.write(f"loadsgf {sgf_file}\n")
            f.write("final_score\n")
            f.write("quit\n")
        
        # Запуск
        cmd = f'type "{cmd_file}" | "{gnugo_path}" --mode gtp --boardsize {board_size} --chinese-rules --komi 6.5'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=None
        )
        
        # Парсинг результата
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('='):
                result_str = line[1:].strip()
                
                if result_str.startswith('B+'):
                    return 1  # чёрные победили
                elif result_str.startswith('W+'):
                    return 2  # белые победили
                elif result_str == '0' or 'jigo' in result_str.lower():
                    return 0  # ничья
        
        return -1  # не удалось определить
        
    except Exception as e:
        print(f"❌ Ошибка при определении победителя: {e}")
        return -1
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_score(sgf_content: str, board_size: int = 19) -> dict:
    """
    Возвращает словарь с очками: {'black': X, 'white': Y, 'diff': Z}
    или None при ошибке
    """
    if not os.path.exists(gnugo_path):
        print(f"❌ GNU Go не найден: {gnugo_path}")
        return None
    
    temp_dir = tempfile.mkdtemp()
    try:
        sgf_file = os.path.join(temp_dir, "game.sgf")
        with open(sgf_file, 'w', encoding='utf-8') as f:
            f.write(sgf_content)
        
        # Используем estimate_score для живых групп + territory для деталей
        cmd_file = os.path.join(temp_dir, "commands.txt")
        with open(cmd_file, 'w') as f:
            f.write(f"loadsgf {sgf_file}\n")
            f.write("estimate_score\n")  # оценка территории
            f.write("final_score\n")    # финальный счёт
            f.write("quit\n")
        
        cmd = f'type "{cmd_file}" | "{gnugo_path}" --mode gtp --boardsize {board_size} --chinese-rules --komi 6.5'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=None
            
        )
        
        scores = {'black': 0, 'white': 0, 'komi': 6.5, 'diff': 0, 'winner': 0}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            
            # Парсим estimate_score (пример: "= Black wins by 12.5 points")
            if 'estimate_score' in line.lower() or ('black' in line.lower() and 'wins by' in line.lower()):
                # Можно извлечь примерную разницу
                match = re.search(r'(\d+\.?\d*)', line)
                if match:
                    scores['estimated_diff'] = float(match.group(1))
            
            # Парсим final_score (пример: "= B+12.5" или "= W+3.5")
            if line.startswith('=') and ('B+' in line or 'W+' in line or line.strip() == '= 0'):
                result_str = line[1:].strip()
                
                if result_str.startswith('B+'):
                    margin = float(result_str[2:])
                    scores['winner'] = 1
                    scores['diff'] = margin
                    # Приблизительно: чёрные получили коми + разницу
                    scores['black'] = margin + 6.5  # условно
                    scores['white'] = 6.5
                    
                elif result_str.startswith('W+'):
                    margin = float(result_str[2:])
                    scores['winner'] = 2
                    scores['diff'] = margin
                    scores['white'] = margin + 6.5
                    scores['black'] = 0
                    
                elif result_str == '0':
                    scores['winner'] = 0
                    scores['diff'] = 0
                    scores['black'] = 6.5
                    scores['white'] = 6.5
        
        return scores if scores['winner'] != 0 or scores['diff'] != 0 else None
        
    except Exception as e:
        print(f"❌ Ошибка при подсчёте очков: {e}")
        return None
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

def get_score_simple(sgf_content: str, board_size: int = 19) -> float:
    scores = get_score(sgf_content, board_size)
    if not scores:
        return 0.0
    
    if scores['winner'] == 1:
        return scores['diff']  # +X чёрные побеждают
    elif scores['winner'] == 2:
        return -scores['diff']  # -X белые побеждают
    return 0.0  # ничья