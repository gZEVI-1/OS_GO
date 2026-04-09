from console_back import *

def run_pvp_game():
    """Запускает игру PvP"""
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
    black_name = input("Черные: ")
    black_name = black_name.strip()
    white_name = input("Белые: ")
    white_name = white_name.strip()

    # Создаем сессию
    session = create_pvp_session(size, black_name, white_name)
    
    if not session.start():
        print("Не удалось запустить игру")
        input("\nНажмите Enter...")
        return
    
    #игра
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
                # time.sleep(1.5)
            elif result.get('undo'):
                print(f"\n {result['message']}")
                # time.sleep(0.5)
            # elif result['success'] and not result.get('game_over'):
            #     # Показываем результат хода
            #     if result.get('bot_move'):
            #         bot_move = result['bot_move']
            #         print(f"\n {bot_move['player_name']} сходил в {bot_move['coord_str']}")
            #         time.sleep(1)
           
        
        # Игра окончена
        if session.game.is_game_over():
            clear_screen()
            print_game_state(session)
            
            # Анализируем результат
            gnugo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                       "bot", "gnugo-3.8", "gnugo.exe")
            
            if os.path.exists(gnugo_path):
                print("\n Анализ позиции...")
                analyzer = gnugo.GnuGoAnalyzer(gnugo_path=gnugo_path)
                try:
                    result = session.get_game_result(analyzer)
                    show_game_result(session, result)
                finally:
                    analyzer.cleanup()
            else:
                show_game_result(session)
        
        input("\nНажмите Enter для возврата в меню...")
        
    finally:
        session.stop()
