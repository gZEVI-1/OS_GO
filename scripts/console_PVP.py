# console_PVP.py
from console_back import *
from KataGoAdapter import KataGoGameAnalyzer, add_katago_analysis_to_session
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core_adapter import create_pvp_session
def run_pvp_game():
    """Запускает игру PvP с поддержкой KataGo анализа"""
    clear_screen()
    print("=" * 60)
    print("         ИГРА ДВУХ ИГРОКОВ (PvP)")
    print("=" * 60)
    
    # Выбор размера доски
    while True:
        try:
            size_input = input("\nВыберите размер доски (9, 13, 19) [19]: ").strip()
            size = int(size_input) if size_input else 19
            if size in [9, 13, 19]:
                break
            print("❌ Размер должен быть 9, 13 или 19")
        except ValueError:
            print("❌ Введите число")

    print("\n📜 Выберите правила:")
    print("1. Китайские (подсчёт по площади, коми 6.5) [по умолчанию]")
    print("2. Японские (подсчёт по территории, коми 6.5)")
    
    rulez = go.Rules.Chinese  # default
    komi = 6.5
    
    while True:
        choice = input("Ваш выбор (1-2) [1]: ").strip() or "1"
        if choice == '1':
            rulez = go.Rules.Chinese
            komi = 6.5
            break
        elif choice == '2':
            rulez = go.Rules.Japanese
            komi = 6.5  # или 0.5 для японских, если хотите
            break
        else:
            print("❌ Выберите 1 или 2")        
    
    # Имена игроков
    print("\n📝 Введите имена игроков:")
    black_name = input("Черные: ").strip() or "Игрок 1"
    white_name = input("Белые: ").strip() or "Игрок 2"
    
    # Создаем сессию
    session = create_pvp_session(size, black_name, white_name, rules = rulez)
    
    print(f"\n✅ Игра: {size}x{size}, правила: {'Китайские' if rulez == go.Rules.Chinese else 'Японские'}")
    # Callback для анализа KataGo
    def on_katago_analysis(result):
        print("\n" + "=" * 60)
        print("📊 АНАЛИЗ ОТ KATAGO")
        print("=" * 60)
        print(f"🏆 Победитель: {result.winner}")
        print(f"📈 Счет: {result.full_result}")
        print(f"⚫ Черные: {result.black_score:.1f}")
        print(f"⚪ Белые: {result.white_score:.1f}")
        
        if result.best_move:
            print(f"\n💡 Лучший ход партии: {result.best_move}")
        
        if result.top_moves:
            print(f"\n🎯 Топ-5 ходов: {', '.join(result.top_moves[:5])}")
    
    # Добавляем анализатор к сессии
    add_katago_analysis_to_session(session, on_katago_analysis)
    
    if not session.start():
        print("❌ Не удалось запустить игру")
        input("\nНажмите Enter...")
        return
    
    # Игровой цикл
    try:
        while session.game_active and not session.game.is_game_over():
            clear_screen()
            print_game_state(session)
            
            state = session.get_current_state()
            
            move_input = get_human_move_input(
                state['current_player_name'],
                state['move_number'],
                state['board_size']
            )
            
            if move_input.lower() == 'help':
                show_help()
                input("\nНажмите Enter для продолжения...")
                continue
            
            result = session.make_human_move(move_input)
            
            if result.get('quit'):
                print("\n👋 Игра прервана.")
                break
            
            if not result['success']:
                print(f"\n❌ {result['message']}")
            elif result.get('undo'):
                print(f"\n↩️ {result['message']}")
        
        # Показываем результат (анализ уже через callback)
        if session.game.is_game_over():
            show_game_result(session)
        
        input("\nНажмите Enter для возврата в меню...")
        
    finally:
        session.stop()