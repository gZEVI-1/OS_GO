from console_back import *

def run_pve_game():
    """Запускает игру против GNUGo"""

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
    
    if not session.start():
        print("❌ Не удалось запустить игру")
        input("\nНажмите Enter...")
        return
    
    # Игровой цикл
    try:
        while session.game_active and not session.game.is_game_over():
            clear_screen()
            print_game_state(session)
            
            state = session.get_current_state()#текущее состояние игры
            
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
                    # time.sleep(1.5)
                elif result.get('undo'):
                    print(f"\n {result['message']}")
                    # time.sleep(0.5)
                elif result['success'] and not result.get('game_over'):
                    # Показываем результат хода человека
                    print(f"\n Ход выполнен")
                    
                    # Если есть ответ бота
                    if result.get('bot_move'):
                        bot_move = result['bot_move']
                        print(f"🤖 {bot_move['player_name']} сходил в {bot_move['coord_str']}")
                        time.sleep(0.2)
            else:
                # Ход бота
                print(f"\n🤔 {state['current_player_name']} думает...")
                time.sleep(0.5)
                
                # Бот ходит автоматически через make_human_move (который вызовет _make_bot_move)
                pass
        
        # Игра окончена
        if session.game.is_game_over():
            clear_screen()
            print_game_state(session)
            
            print("\n Анализ позиции...")
            analyzer = gnugo.GnuGoAnalyzer(gnugo_path=gnugo_path)
            try:
                result = session.get_game_result(analyzer)
                show_game_result(session, result)
                
                if result:
                    winner = result.get('winner')
                    player_is_black = (player_color == go.Color.Black)
                    
                    if (winner == "Черные" and player_is_black) or \
                       (winner == "Белые" and not player_is_black):
                        print("\n ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!")
                    elif winner != "Ничья":
                        print("\n GNU Go победил")
                    else:
                        print("\n Ничья!")
                        
            finally:
                analyzer.cleanup()
        
        input("\nНажмите Enter для возврата в меню...")
        
    finally:
        session.stop()