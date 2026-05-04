
import os
import sys
import time
import go_engine as go
from core_adapter import (
    GameSession, PlayerType, CoordinateUtils,
    create_pvp_session, create_pve_session
)
import GnuGo_Analyzer as gnugo
import config as cfg
from gnugo_adapter import GNUGoBot

def clear_screen():
    """Очищает экран консоли"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_stone_symbol(color: go.Color, is_hoshi: bool = False) -> str:
    """Возвращает символ для отображения камня или точки"""
    if color == go.Color.Black:
        return "○"
    elif color == go.Color.White:
        return "●"
    else:
        return "+" if is_hoshi else "·"


def is_hoshi_point(x: int, y: int, size: int) -> bool:
    """Проверяет, является ли точка хоси """
    if size == 19:
        return (x in [3, 9, 15] and y in [3, 9, 15])
    elif size == 13:
        return (x in [3, 9] and y in [3, 9]) or  (x == 6 and y==6) 
    elif size == 9:
        return (x in [2, 6] and y in [2, 6]) or (x==4 and y==4)
    return False


def print_board(board):
    """Выводит доску в консоль"""
    size = board.get_size()
    
    # Заголовок
    print("   ", end="")
    for i in range(size):
        letter = CoordinateUtils.index_to_letter(i)
        print(f"{letter:2}", end="")
    print()
    
    # доска
    for y in range(size):
        print(f"{y+1:2} ", end="")
        
        for x in range(size):
            color = board.get_color(x, y)
            is_hoshi = is_hoshi_point(x, y, size)
            symbol = get_stone_symbol(color, is_hoshi)
            print(f"{symbol} ", end="")
        print()


def print_game_state(session: GameSession): #шушера 
    """Выводит текущее состояние игры"""
    state = session.get_current_state()
    board = state['board']
    
    print("=" * 60)
    mode_str = "PvP" if all(p['type'] == PlayerType.HUMAN 
                             for p in session.players.values()) else "PvE"
    print(f"           ИГРА ГО ({state['board_size']}x{state['board_size']}) — {mode_str}")
    print("=" * 60)
    print(f"📊 Ход номер: {state['move_number']}")
    
    player_symbol = "○" if state['current_player'] == go.Color.Black else "●"
    player_type = " (Бот)" if state['current_player_type'] == PlayerType.GNU_GO else ""
    print(f"🎮 Текущий игрок: {player_symbol} {state['current_player_name']}{player_type}")
    print(f"🔄 Пасов подряд: {state['passes']}")
    print("-" * 60)
    
    print_board(board)


def print_legal_moves(session: GameSession):
    """Выводит доску с отмеченными легальными ходами (для отладки)"""

    legal_board = session.get_legal_moves()
    size = legal_board.get_size()
    
    print("\n   ", end="")
    for i in range(size):
        letter = CoordinateUtils.index_to_letter(i)
        print(f"{letter:2}", end="")
    print(" (X = легальный ход)")
    
    for y in range(size):
        print(f"{y+1:2} ", end="")
        for x in range(size):
            color = legal_board.get_color(x, y)
            if color == go.Color.Black:
                print("X ", end="")
            else:
                print("·", end="")
        print()


def get_human_move_input(player_name: str, move_number: int, board_size: int) -> str:
    """Запрашивает ввод хода у человека"""

    print(f"\n{player_name}, ваш ход (номер хода: {move_number})")
    print("Введите координаты (например, D4), 'pass' для паса, 'undo' для отмены, 'quit' для выхода:")
    
    try:
        move_input = input("> ").strip()
        return move_input
    except KeyboardInterrupt:
        return "quit"


def show_game_result(session: GameSession, result: dict = None):
    """Показывает результат игры"""

    print("\n" + "=" * 60)
    print("🏆 ИГРА ОКОНЧЕНА!")
    print("=" * 60)
    
    if result:
        print(f"\n Победитель: {result.get('winner', 'Неизвестно')}")
        print(f" Счет: {result.get('full_result', 'N/A')}")
        if 'margin' in result:
            print(f" Разница: {result['margin']} очков")
    else:
        print("\n Игра завершена (два паса подряд)")
    
    # Сохраняем игру
    mode = "pvp" if all(p['type'] == PlayerType.HUMAN 
                        for p in session.players.values()) else "pve"
    filepath = session.save_game(game_mode=mode)
    if filepath:
        print(f"\n💾 Игра сохранена: {filepath}")


def show_help():
    """Показывает справку по командам"""
    print("""
Справка по командам:
          
  • D4, Q16 и т.д. — координаты хода (буква + число)
  • pass — пропустить ход
  • undo — отменить последний ход
  • quit — выход из игры
  • help — показать эту справку

  Буква 'I' не используется в координатах!
""")




def test_gnugo_connection():
    """Тестирует соединение с GNU Go"""
    clear_screen()
    print("=" * 60)
    print("         ТЕСТ СОЕДИНЕНИЯ С GNU GO")
    print("=" * 60)
    
    # Правильный путь
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gnugo_path = os.path.join(base_dir, "bot", "gnugo-3.8", "gnugo.exe")
    
    print(f"\n📁 Путь к GNU Go: {gnugo_path}")
    print(f"📁 Файл существует: {os.path.exists(gnugo_path)}")
    
    if not os.path.exists(gnugo_path):
        print("❌ GNU Go не найден!")
        input("\nНажмите Enter...")
        return
    
    # Проверяем запуск
    print("\n🔄 Запуск GNU Go...")
    bot = GNUGoBot(gnugo_path, board_size=9)
    
    if not bot.start():
        print("❌ Не удалось запустить GNU Go")
        input("\nНажмите Enter...")
        return
    
    print("✅ GNU Go запущен")
    
    try:
        # Получаем тестовый ход
        print("\n🔄 Получение тестового хода...")
        move = bot.get_move('B')
        
        if move:
            if move['is_pass']:
                print("🤖 GNU Go сходил: PASS")
            else:
                coord = CoordinateUtils.format_move(move['x'], move['y'])
                print(f"🤖 GNU Go сходил: {coord}")
            print("\n✅ Тест завершен успешно!")
        else:
            print("⚠️ Не удалось получить ход")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        bot.stop()
        print("🛑 GNU Go остановлен")
    
    input("\nНажмите Enter...")


def test_katago_connection():
    """Тестирует соединение с KataGo"""
    clear_screen()
    print("=" * 60)
    print("         ТЕСТ СОЕДИНЕНИЯ С KATAGO")
    print("=" * 60)
    
    print("\n🔍 Проверка доступности KataGo...")
    
    # Проверяем доступность (автоопределение путей)
    if not go.KataGoAnalyzer.is_available(""):
        print("❌ KataGo не найден. Проверьте пути:")
        print("   bot\\KataGo-1.16.4-OpenCL\\katago.exe")
        print("   bot\\katago\\katago.exe")
        input("\nНажмите Enter...")
        return
    
    print("✅ Исполняемый файл найден")
    
    print("\n🔄 Инициализация KataGo (может занять время при первом запуске)...")
    analyzer = go.KataGoAnalyzer()
    
    try:
        if not analyzer.initialize():
            print("❌ Не удалось инициализировать KataGo")
            input("\nНажмите Enter...")
            return
        
        print("✅ KataGo инициализирован и отвечает")
        
        # Тестовый анализ простой позиции
        print("\n🔄 Тестовый анализ позиции...")
        test_sgf = "(;GM[1]FF[4]SZ[9]PB[Black]PW[White]KM[6.5]RU[Chinese];B[ee];W[de])"
        
        result = analyzer.analyze_sgf(test_sgf, 9, 6.5)
        
        if result.success:
            print("\n📊 РЕЗУЛЬТАТ ТЕСТА:")
            print(f"   Победитель: {result.winner}")
            print(f"   Отрыв: {result.score_lead}")
            print(f"   Черные: {result.black_score:.1f}")
            print(f"   Белые: {result.white_score:.1f}")
            print("\n✅ Тест завершен успешно!")
        else:
            print(f"\n⚠️ Анализ вернул ошибку: {result.error_message}")
            print("   Но процесс KataGo запущен и отвечает на команды.")
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        analyzer.shutdown()
        print("\n🛑 KataGo остановлен")
    
    input("\nНажмите Enter...")

