import subprocess
import os
import tempfile
import re
import time
gnugo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot", "gnugo-3.8", "gnugo.exe")
class GnuGoAnalyzer:
    def __init__(self, gnugo_path):
        """
        Инициализация анализатора GNU Go
        :param gnugo_path: путь к исполняемому файлу GNU Go
        """
        self.gnugo_path = gnugo_path
        self.temp_dir = os.path.join(tempfile.gettempdir(), f"gnugo_analysis_{int(time.time())}")
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
            timeout=5
        )
        return result.returncode == 0
    except:
        return False