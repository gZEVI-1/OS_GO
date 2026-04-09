# console_PVE.py
from console_back import *
from scripts.KataGoAdapter import KataGoGameAnalyzer, add_katago_analysis_to_session


def run_pve_game():
    """Запускает игру против GNU Go с поддержкой KataGo анализа"""
    
    clear_screen()
    print("=" * 60)
    print("         ИГРА ПРОТИВ GNU GO (PvE)")
    print("=" * 60)
    
    # Проверяем наличие GNU Go
    gnugo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                               "bot", "gnugo-3.8", "gnugo.exe")
    
    if not os.path.exists(gnugo_path):
        print(f"\n❌ GNU Go не найден по пути: {gnugo_path}")
        input("\nНажмите Enter для возврата...")
        return
    
    print("\n Правила игры:")
    print("  • Введите координаты в формате 'D4'")
    print("  • Введите 'pass' для пропуска хода")
    print("  • Введите 'quit' для выхода из игры")
    print("  • Игра заканчивается после двух пасов подряд\n")
    
    # Выбор размера доски
    while True:
        try:
            size_input = input("Выберите размер доски (9, 13, 19) [19]: ").strip()
            size = int(size_input) if size_input else 19
            if size in [9, 13, 19]:
                break
            print("❌ Размер должен быть 9, 13 или 19")
        except ValueError:
            print("❌ Введите число")
    
    # Выбор цвета
    print("\n Выберите цвет:")
    print("1. Играть черными (первые)")
    print("2. Играть белыми (вторые)")
    
    while True:
        choice = input("Ваш выбор (1-2) [1]: ").strip() or "1"
        if choice == '1':
            player_color = go.Color.Black
            break
        elif choice == '2':
            player_color = go.Color.White
            break
        else:
            print("❌ Выберите 1 или 2")
    
    player_name = input("\nВаше имя : ").strip() or "user"
    bot_name = "GNU Go"
    
    # Создаем сессию
    session = create_pve_session(size, player_color, player_name, gnugo_path)
    
    # Добавляем KataGo анализ
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
        
        # Определяем победителя для вывода сообщения
        player_is_black = (player_color == go.Color.Black)
        if (result.winner == "Черные" and player_is_black) or \
           (result.winner == "Белые" and not player_is_black):
            print("\n🎉 ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!")
        elif result.winner != "Ничья":
            print("\n🤖 GNU Go победил")
        else:
            print("\n🤝 Ничья!")
    
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
            
            if state['current_player_type'] == PlayerType.HUMAN:
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
                    print(f"\n {result['message']}")
                elif result['success'] and not result.get('game_over'):
                    if result.get('bot_move'):
                        bot_move = result['bot_move']
                        print(f"\n🤖 {bot_move['player_name']} сходил в {bot_move['coord_str']}")
            else:
                # Ход бота происходит автоматически через make_human_move
                pass
        
        input("\nНажмите Enter для возврата в меню...")
        
    finally:
        session.stop()