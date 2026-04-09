
"""
Анализатор партий с использованием KataGo (C++ биндинги)
"""

import os
import sys
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
KATAGO_PATH = os.path.join(BASE_DIR, "bot", "katago", "katago.exe")
KATAGO_MODEL = os.path.join(BASE_DIR, "bot", "katago", "models", "kata1.bin.gz")
KATAGO_CONFIG = os.path.join(BASE_DIR, "bot", "katago", "analysis_windows.cfg")

KATAGO_AVAILABLE = False

try:
    import go_engine as go
    
    if hasattr(go, 'KataGoAnalyzer'):
        if os.path.exists(KATAGO_PATH) and os.path.exists(KATAGO_MODEL):
            KATAGO_AVAILABLE = True
            print("✅ KataGo доступен для анализа")
        else:
            print(f"⚠️ KataGo не найден: {KATAGO_PATH}")
            print(f"⚠️ Модель не найдена: {KATAGO_MODEL}")
    else:
        print("⚠️ Модуль KataGoAnalyzer не найден в go_engine")
except ImportError as e:
    print(f"⚠️ Не удалось импортировать go_engine: {e}")
except Exception as e:
    print(f"⚠️ Ошибка инициализации KataGo: {e}")


@dataclass
class KataGoAnalysisResult:
    """Результат анализа партии KataGo"""
    success: bool = False
    winner: str = ""  # "Черные", "Белые", "Ничья"
    margin: float = 0.0
    full_result: str = ""
    black_score: float = 0.0
    white_score: float = 0.0
    winrate: float = 0.5
    best_move: str = ""
    best_move_number: int = 0
    best_move_improvement: float = 0.0
    top_moves: List[str] = field(default_factory=list)
    critical_moments: List[Dict] = field(default_factory=list)
    winrate_history: List[Dict] = field(default_factory=list)
    error_message: str = ""


class KataGoAnalyzer:
    """
    Анализатор партий с использованием KataGo через C++ биндинги
    """
    
    def __init__(self):
        self._analyzer = None
        self._initialized = False
    
    def _init_analyzer(self, board_size: int = 19, komi: float = 6.5) -> bool:
        """Инициализирует C++ анализатор"""
        if not KATAGO_AVAILABLE:
            return False
        
        try:
            import go_engine as go
            
            config = go.KataGoConfig()
            config.katago_path = KATAGO_PATH
            config.model_path = KATAGO_MODEL
            config.config_path = KATAGO_CONFIG
            config.board_size = board_size
            config.komi = komi
            config.max_visits = 500
            config.analysis_mode = "kata-analyze"
            
            self._analyzer = go.KataGoAnalyzer()
            if self._analyzer.initialize(config):
                self._initialized = True
                return True
            else:
                self._analyzer = None
                return False
                
        except Exception as e:
            print(f"⚠️ Ошибка инициализации KataGo: {e}")
            self._analyzer = None
            return False
    
    def analyze_sgf(self, sgf_content: str, board_size: int = 19, komi: float = 6.5) -> Optional[KataGoAnalysisResult]:
        """
        Анализирует SGF файл и возвращает результат
        
        Args:
            sgf_content: содержимое SGF файла
            board_size: размер доски
            komi: значение коми
            
        Returns:
            KataGoAnalysisResult с результатами анализа
        """
        result = KataGoAnalysisResult()
        
        if not KATAGO_AVAILABLE:
            result.error_message = "KataGo не доступен"
            return result
        
        if not self._initialized:
            if not self._init_analyzer(board_size, komi):
                result.error_message = "Не удалось инициализировать KataGo"
                return result
        
        try:
            cpp_result = self._analyzer.analyze_sgf(sgf_content, board_size, komi)
            
            if cpp_result and cpp_result.success:
                result.success = True
                result.winner = "Черные" if cpp_result.winner == "Black" else ("Белые" if cpp_result.winner == "White" else "Ничья")
                result.margin = abs(cpp_result.score_lead)
                result.full_result = f"{'B' if cpp_result.winner == 'Black' else 'W'}+{abs(cpp_result.score_lead)}"
                result.black_score = cpp_result.black_score
                result.white_score = cpp_result.white_score
                result.winrate = cpp_result.winrate
                result.best_move = cpp_result.best_move
                result.top_moves = cpp_result.top_moves[:5] if cpp_result.top_moves else []
                
                winrate_history = self._get_winrate_history(sgf_content, board_size, komi)
                if winrate_history:
                    result.winrate_history = winrate_history
                    result.critical_moments = self._find_critical_moments(winrate_history)
                    
                    best = self._find_best_move_in_history(winrate_history)
                    if best:
                        result.best_move_number = best['move_number']
                        result.best_move_improvement = best['improvement']
            else:
                result.error_message = cpp_result.error_message if cpp_result else "Неизвестная ошибка"
            
            return result
            
        except Exception as e:
            result.error_message = str(e)
            return result
    
    def _get_winrate_history(self, sgf_content: str, board_size: int, komi: float) -> Optional[List[Dict]]:
        """Получает историю winrate по ходам"""
        try:
            import re
            
            moves = []
            pattern = r';([BW])\[([a-z]{0,2})\]'
            
            for match in re.finditer(pattern, sgf_content):
                color = match.group(1)
                coord = match.group(2)
                
                if coord and len(coord) >= 2:
                    x = ord(coord[0]) - ord('a')
                    if x >= 8:
                        x -= 1
                    y = ord(coord[1]) - ord('a')
                    if y >= 8:
                        y -= 1
                    letter = chr(65 + x + (1 if x >= 8 else 0))
                    moves.append(f"{color} {letter}{y + 1}")
                else:
                    moves.append(f"{color} pass")
            
            if not moves:
                return None
            
            history = []
            moves_sequence = []
            previous_winrate = 0.5
            
            for i, move in enumerate(moves):
                moves_sequence.append(move)
                
                analysis = self._analyzer.analyze_position(moves_sequence, board_size, komi, 200)
                
                if analysis and analysis.success:
                    winrate = analysis.winrate
                    if i % 2 == 1:  # ход белых
                        winrate = 1 - winrate
                    
                    history.append({
                        'move_number': i + 1,
                        'move': move,
                        'winrate': winrate,
                        'score_lead': analysis.score_lead if i % 2 == 0 else -analysis.score_lead,
                        'change': winrate - previous_winrate,
                        'is_critical': abs(winrate - previous_winrate) > 0.15
                    })
                    
                    previous_winrate = winrate
            
            return history
            
        except Exception as e:
            print(f"⚠️ Ошибка получения истории winrate: {e}")
            return None
    
    def _find_critical_moments(self, history: List[Dict], top_n: int = 5) -> List[Dict]:
        """Находит ключевые моменты партии"""
        critical = [h for h in history if h.get('is_critical', False)]
        critical.sort(key=lambda x: abs(x.get('change', 0)), reverse=True)
        
        result = []
        for moment in critical[:top_n]:
            result.append({
                'move_number': moment['move_number'],
                'move': moment['move'],
                'winrate_before': moment['winrate'] - moment.get('change', 0),
                'winrate_after': moment['winrate'],
                'change': abs(moment.get('change', 0)),
                'who_benefited': 'Черные' if moment.get('change', 0) > 0 else 'Белые',
                'significance': 'high' if abs(moment.get('change', 0)) > 0.25 else 'medium'
            })
        
        return result
    
    def _find_best_move_in_history(self, history: List[Dict]) -> Optional[Dict]:
        """Находит ход, который больше всего улучшил позицию"""
        best = None
        best_improvement = 0
        
        for h in history:
            improvement = h.get('change', 0)
            if improvement > best_improvement:
                best_improvement = improvement
                best = {
                    'move_number': h['move_number'],
                    'move': h['move'],
                    'improvement': improvement
                }
        
        return best
    
    def analyze_position(self, moves: List[str], board_size: int = 19, komi: float = 6.5, max_visits: int = 200) -> Optional[Dict]:
        """
        Анализирует текущую позицию
        
        Args:
            moves: список ходов в формате ["B D4", "W Q16", ...]
            board_size: размер доски
            komi: значение коми
            max_visits: максимальное количество визитов
            
        Returns:
            Словарь с winrate и score_lead
        """
        if not self._initialized:
            if not self._init_analyzer(board_size, komi):
                return None
        
        try:
            return self._analyzer.analyze_position(moves, board_size, komi, max_visits)
        except Exception as e:
            print(f"⚠️ Ошибка анализа позиции: {e}")
            return None
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self._analyzer:
            try:
                self._analyzer.shutdown()
            except:
                pass
            self._analyzer = None
        self._initialized = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()


def quick_analyze(sgf_content: str, board_size: int = 19) -> Optional[KataGoAnalysisResult]:
    """Быстрый анализ SGF через KataGo"""
    with KataGoAnalyzer() as analyzer:
        return analyzer.analyze_sgf(sgf_content, board_size)


def is_available() -> bool:
    """Проверяет доступность KataGo"""
    return KATAGO_AVAILABLE