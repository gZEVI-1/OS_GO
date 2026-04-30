"""
Простой Python-адаптер для KataGo (C++ ядро)
"""

import go_engine as go
from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class KataGoAnalysisResult:
    success: bool = False
    winner: str = ""
    margin: float = 0.0
    full_result: str = ""
    black_score: float = 0.0
    white_score: float = 0.0
    winrate: float = 0.5
    best_move: str = ""
    top_moves: List[str] = field(default_factory=list)
    error_message: str = ""


class KataGoAnalyzer:
    """
    Простой анализатор
    """
    
    def __init__(self):
        self._cpp = go.KataGoAnalyzer()
    
    def initialize(self) -> bool:
        """Инициализация """
        return self._cpp.initialize()
    
    def analyze_sgf(self, sgf_content: str, board_size: int = 19, komi: float = 6.5) -> Optional[KataGoAnalysisResult]:
        result = KataGoAnalysisResult()
        
        try:
            cpp_result = self._cpp.analyze_sgf(sgf_content, board_size, komi)
            
            if cpp_result.success:
                result.success = True
                result.winner = "Черные" if cpp_result.winner == "Black" else "Белые"
                result.margin = abs(cpp_result.score_lead)
                result.full_result = f"{cpp_result.winner} +{result.margin}"
                result.black_score = cpp_result.black_score
                result.white_score = cpp_result.white_score
                result.winrate = cpp_result.winrate
                result.best_move = cpp_result.best_move
                result.top_moves = list(cpp_result.top_moves) if cpp_result.top_moves else []
            else:
                result.error_message = cpp_result.error_message
                
        except Exception as e:
            result.error_message = str(e)
            
        return result
    
    def cleanup(self):
        self._cpp.shutdown()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()


def is_available() -> bool:
    return go.KataGoAnalyzer.is_available("")

def set_paths(katago_path: str, model_path: str, config_path: str = ""):
    """Установка путей (если автоопределение не сработало)"""
    go.KataGoAnalyzer.set_default_paths(katago_path, model_path, config_path)

def quick_analyze(sgf_content: str) -> Optional[KataGoAnalysisResult]:
    """Быстрый анализ одной строкой"""
    with KataGoAnalyzer() as analyzer:
        if analyzer.initialize():
            return analyzer.analyze_sgf(sgf_content)
    return None