
"""
Адаптер для интеграции KataGo в игровые сессии
"""

from typing import Optional, Callable
from KataGoAnalyzer import KataGoAnalyzer, KataGoAnalysisResult, is_available


class KataGoGameAnalyzer:
    """Анализатор для игровых сессий"""
    
    def __init__(self, session=None):
        self.session = session
        self._analyzer: Optional[KataGoAnalyzer] = None
        self._initialized: bool = False
    
    def initialize(self) -> bool:
        """Инициализация с автоопределением"""
        # if not is_available():
        #     print("❌ KataGo не доступен")
        #     return False
        
        self._analyzer = KataGoAnalyzer()
        self._initialized = self._analyzer.initialize()
        # if self._initialized:
        #     print("✅ KataGo инициализирован")
        # else:
        #     print("❌ KataGo не доступен")
        return self._initialized
    
    def analyze_current_game(self) -> Optional[KataGoAnalysisResult]:
        """Анализирует текущую игру"""
        if not self.session:
            # print("❌ Нет активной сессии")
            return None
        
        if not self._initialized and not self.initialize():
            return None
        
        if self._analyzer is None:
            return None
        
        try:
            sgf = self.session.game.get_sgf()
            return self._analyzer.analyze_sgf(sgf, self.session.board_size, self.session.komi)
        except Exception as e:
            # print(f"❌ Ошибка анализа: {e}")
            return None
    
    def print_analysis(self, result: KataGoAnalysisResult) -> None:
        """Вывод результатов анализа"""
        if not result.success:
            # print(f"\n❌ Ошибка анализа: {result.error_message}")
            return
        
        print("\n" + "=" * 60)
        print("📊 АНАЛИЗ KATAGO")
        print("=" * 60)
        print(f"🏆 Победитель: {result.winner}")
        print(f"📈 Результат: {result.full_result}")
        print(f"⚫ Черные: {result.black_score:.1f}")
        print(f"⚪ Белые: {result.white_score:.1f}")
        
        if result.best_move:
            print(f"💡 Лучший ход: {result.best_move}")
        
        if result.top_moves:
            print(f"🎯 Топ-5 ходов: {', '.join(result.top_moves[:5])}")
    
    def cleanup(self) -> None:
        if self._analyzer:
            self._analyzer.cleanup()
            self._analyzer = None
        self._initialized = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()


def add_katago_analysis_to_session(session, on_analysis_complete: Callable = None):
    """Добавляет анализ KataGo к сессии"""
    def enhanced_game_over():
        print("\n🔍 Анализ партии с KataGo...")
        analyzer = KataGoGameAnalyzer(session)
        try:
            if analyzer.initialize():
                result = analyzer.analyze_current_game()
                if result and result.success:
                    if on_analysis_complete:
                        on_analysis_complete(result)
                    else:
                        analyzer.print_analysis(result)
                else:
                    print("\n⚠️ Анализ не выполнен")
            else:
                print("\n⚠️ KataGo недоступен")
        except Exception as e:
            print(f"\n❌ Ошибка анализа: {e}")
        finally:
            analyzer.cleanup()
    
    original = list(session.game_over_callbacks)
    session.game_over_callbacks.clear()
    session.add_game_over_callback(enhanced_game_over)
    for cb in original:
        session.add_game_over_callback(cb)