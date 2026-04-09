# console_PVP.py
from console_back import *
from scripts.KataGoAdapter import KataGoGameAnalyzer, add_katago_analysis_to_session


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
            print(" Размер должен быть 9, 13 или 19")
        except ValueError:
            print(" Введите число")
    
    # Имена игроков
    print("\nВведите имена игроков:")
    black_name = input("Черные: ").strip()
    white_name = input("Белые: ").strip()
    
    # Создаем сессию
    session = create_pvp_session(size, black_name, white_name)
    
    def on_katago_analysis(result):
        """Callback при завершении анализа KataGo"""
        print("\n" + "=" * 60)
        print("📊 АНАЛИЗ ОТ KATAGO")
        print("=" * 60)
        print(f"🏆 Победитель: {result.winner}")
        print(f"📈 Счет: {result.full_result}")
        print(f"⚫ Черные: {result.black_score:.1f} очков")
        print(f"⚪ Белые: {result.white_score:.1f} очков")
        
        if result.best_move:
            print(f"\n🏅 Лучший ход партии: {result.best_move} (ход #{result.best_move_number})")
        
        if result.top_moves:
            print(f"\n🎯 Топ-5 ходов: {', '.join(result.top_moves[:5])}")
    
    # Добавляем анализатор к сессии
    add_katago_analysis_to_session(session, on_katago_analysis)
    
    if not session.start():
        print("Не удалось запустить игру")
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
                print("\n Игра прервана.")
                break
            
            if not result['success']:
                print(f"\n {result['message']}")
            elif result.get('undo'):
                print(f"\n {result['message']}")
        
        # Если игра окончена, но анализатор еще не сработал (через callback)
        if session.game.is_game_over() and not session.game_over_callbacks:
            # Альтернативный способ - прямой анализ
            print("\n Анализ позиции через KataGo...")
            with KataGoGameAnalyzer(session) as katago:
                if katago.initialize(size, 6.5):
                    result = katago.analyze_current_game()
                    if result and result.success:
                        katago.print_analysis(result)
                    else:
                        print("❌ Не удалось выполнить анализ KataGo")
                else:
                    print("⚠️ KataGo не доступен")
            
            show_game_result(session)
        
        input("\nНажмите Enter для возврата в меню...")
        
    finally:
        session.stop()