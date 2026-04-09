
"""
Адаптер для интеграции KataGo анализа в игровые сессии
Не изменяет существующие классы, а расширяет их функциональность
"""

from typing import Optional, Dict, List, Callable

from scripts.KataGoAnalyzer import KataGoAnalyzer, KataGoAnalysisResult, is_available


class KataGoGameAnalyzer:
    """
    Анализатор для игровых сессий с использованием KataGo
    """
    
    def __init__(self, session=None):
        """
        Args:
            session: объект GameSession (опционально)
        """
        self.session = session
        self.analyzer = None
        self._initialized = False
    
    def initialize(self, board_size: int = 19, komi: float = 6.5) -> bool:
        """Инициализирует KataGo анализатор"""
        if not is_available():
            print("❌ KataGo не доступен")
            return False
        
        self.analyzer = KataGoAnalyzer()
        self._initialized = True
        return True
    
    def analyze_current_game(self) -> Optional[KataGoAnalysisResult]:
        """
        Анализирует текущую игру в сессии
        """
        if not self.session:
            print("❌ Нет активной сессии")
            return None
        
        if not self._initialized:
            if not self.initialize(self.session.board_size, self.session.komi):
                return None
        
        sgf_content = self.session.game.get_sgf()
        return self.analyzer.analyze_sgf(sgf_content, self.session.board_size, self.session.komi)
    
    def analyze_sgf(self, sgf_content: str, board_size: int = 19, komi: float = 6.5) -> Optional[KataGoAnalysisResult]:
        """Анализирует SGF файл"""
        if not self._initialized:
            if not self.initialize(board_size, komi):
                return None
        
        return self.analyzer.analyze_sgf(sgf_content, board_size, komi)
    
    def get_winrate_at_position(self, moves: List[str]) -> Optional[float]:
        """
        Получает winrate для текущей позиции
        """
        if not self._initialized or not self.analyzer:
            return None
        
        result = self.analyzer.analyze_position(moves, self.session.board_size, self.session.komi)
        if result:
            return result.get('winrate')
        return None
    
    def print_analysis(self, result: KataGoAnalysisResult):
        """Выводит результат анализа в консоль"""
        if not result.success:
            print(f"\n❌ Ошибка анализа: {result.error_message}")
            return
        
        print("\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТ АНАЛИЗА ПАРТИИ (KataGo)")
        print("=" * 70)
        print(f"🏆 Победитель: {result.winner}")
        print(f"📈 Счет: {result.full_result}")
        print(f"⚫ Черные: {result.black_score:.1f} очков")
        print(f"⚪ Белые: {result.white_score:.1f} очков")
        
        if result.best_move:
            print("\n" + "=" * 70)
            print("🏅 ЛУЧШИЙ ХОД ПАРТИИ")
            print("=" * 70)
            print(f"📍 Ход #{result.best_move_number}: {result.best_move}")
            if result.best_move_improvement > 0:
                print(f"📈 Улучшил вероятность победы на {result.best_move_improvement * 100:.1f}%")
        
        if result.top_moves:
            print("\n" + "=" * 70)
            print("🎯 ТОП-5 ЛУЧШИХ ХОДОВ В ПАРТИИ")
            print("=" * 70)
            for i, move in enumerate(result.top_moves, 1):
                print(f"  {i}. {move}")
        
        if result.critical_moments:
            print("\n" + "=" * 70)
            print("⚠️ КЛЮЧЕВЫЕ МОМЕНТЫ ПАРТИИ")
            print("=" * 70)
            for moment in result.critical_moments[:5]:
                icon = "🔴" if moment['significance'] == 'high' else "🟡"
                print(f"\n{icon} Ход #{moment['move_number']}: {moment['move']}")
                print(f"   Winrate изменился с {moment['winrate_before'] * 100:.1f}% на {moment['winrate_after'] * 100:.1f}%")
                print(f"   Изменение: {moment['change'] * 100:.1f}%")
        
        #шкала
        if result.winrate_history:
            self._print_winrate_scale(result.winrate_history)
    
    def _print_winrate_scale(self, history: List[Dict]):
        """Выводит компактную шкалу winrate"""
        print("\n" + "=" * 70)
        print("📈 ДИНАМИКА WINRATE")
        print("=" * 70)
        
        chars = []
        for h in history:
            wr = h['winrate']
            if wr >= 0.75:
                chars.append("█")
            elif wr >= 0.60:
                chars.append("▓")
            elif wr >= 0.55:
                chars.append("▒")
            elif wr >= 0.45:
                chars.append("░")
            elif wr >= 0.40:
                chars.append("▒")
            elif wr >= 0.25:
                chars.append("▓")
            else:
                chars.append("█")
        
        grouped = []
        for i in range(0, len(chars), 10):
            group = chars[i:i+10]
            grouped.append("".join(group))
        
        print(f"  {' '.join(grouped)}")
        print("  █=высокий winrate черных, ░=низкий winrate черных")
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.analyzer:
            self.analyzer.cleanup()
        self._initialized = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()


def add_katago_analysis_to_session(session, on_analysis_complete: Callable = None):
    """
    Добавляет возможность анализа KataGo к существующей сессии
    
    Args:
        session: объект GameSession
        on_analysis_complete: callback при завершении анализа
    """
    def enhanced_game_over():
        sgf_content = session.game.get_sgf()
        
        with KataGoGameAnalyzer(session) as katago:
            if katago.initialize(session.board_size, session.komi):
                result = katago.analyze_current_game()
                if result and result.success:
                    if on_analysis_complete:
                        on_analysis_complete(result)
                    else:
                        katago.print_analysis(result)
                else:
                    print("\n❌ Не удалось выполнить анализ KataGo")
            else:
                print("\n⚠️ KataGo не доступен, используется GNU Go анализ")
    
    original_callbacks = session.game_over_callbacks.copy()
    session.game_over_callbacks.clear()
    
    session.add_game_over_callback(enhanced_game_over)
    
    for cb in original_callbacks:
        session.add_game_over_callback(cb)