# scripts/sgf_analyzer.py
"""
Модуль для анализа SGF файлов через KataGo (C++ ядро)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import go_engine as go

# Добавляем путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from KataGoAnalyzer import KataGoAnalysisResult


class SGFAnalyzer:
    """Класс для анализа SGF файлов через KataGo"""
    
    def __init__(self):
        self._analyzer: Optional[go.KataGoAnalyzer] = None
        self._initialized = False
        
        # Папки из C++
        self.sgf_dir = Path(go.KataGoAnalyzer.get_loaded_sgf_path())
        self.results_dir = self.sgf_dir.parent / "analysis_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """Инициализация KataGo"""
        if self._initialized:
            return True
            
        try:
            print("🔄 Инициализация KataGo...")
            self._analyzer = go.KataGoAnalyzer()
            self._initialized = self._analyzer.initialize()
            
            if self._initialized:
                print("✅ KataGo готов к работе")
            else:
                print("❌ Не удалось инициализировать KataGo")
            
            return self._initialized
        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            return False
    
    def get_sgf_files(self) -> List[go.SGFInfo]:
        """Получить список SGF файлов"""
        return go.KataGoAnalyzer.list_sgf_files()
    
    def analyze_file(self, filepath: str, board_size: int = -1, komi: float = -1.0) -> Optional[KataGoAnalysisResult]:
        """Анализировать один SGF файл"""
        if not self._initialized and not self.initialize():
            return None
        
        filename = Path(filepath).name
        print(f"\n🔍 Анализ: {filename}")
        print("⏳ Подождите, это может занять несколько секунд...")
        
        try:
            cpp_result = self._analyzer.analyze_sgf_file(filepath, board_size, komi)
            
            result = KataGoAnalysisResult()
            result.success = cpp_result.success
            result.error_message = cpp_result.error_message
            
            if cpp_result.success:
                result.winner = "Черные" if cpp_result.winner == "Black" else "Белые"
                result.margin = abs(cpp_result.score_lead)
                result.full_result = f"{cpp_result.winner} +{result.margin:.1f}"
                result.black_score = cpp_result.black_score
                result.white_score = cpp_result.white_score
                result.winrate = cpp_result.winrate
                result.best_move = cpp_result.best_move
                result.top_moves = list(cpp_result.top_moves) if cpp_result.top_moves else []
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
            return None
    
    def save_result(self, filename: str, result: KataGoAnalysisResult) -> Optional[Path]:
        """Сохранить результат анализа"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.results_dir / f"{filename}_{timestamp}.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("РЕЗУЛЬТАТ АНАЛИЗА KATAGO\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Файл: {filename}.sgf\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if result.success:
                    f.write(f"🏆 Победитель: {result.winner}\n")
                    f.write(f"📊 Счет: {result.full_result}\n")
                    f.write(f"⚫ Черные: {result.black_score:.1f}\n")
                    f.write(f"⚪ Белые: {result.white_score:.1f}\n")
                    f.write(f"📈 Отрыв: {result.margin:.1f}\n")
                    f.write(f"🎲 Winrate: {result.winrate:.3f}\n")
                    
                    if result.best_move:
                        f.write(f"\n💡 Лучший ход: {result.best_move}\n")
                    
                    if result.top_moves:
                        f.write(f"\n🎯 Топ ходов:\n")
                        for i, move in enumerate(result.top_moves[:10], 1):
                            f.write(f"   {i}. {move}\n")
                else:
                    f.write(f"❌ Ошибка: {result.error_message}\n")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return None
    
    def cleanup(self):
        """Очистка"""
        if self._analyzer:
            self._analyzer.shutdown()
            self._analyzer = None
        self._initialized = False