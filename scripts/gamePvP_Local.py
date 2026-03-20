import go_engine as go
import os
import time
import GnuGo_Integration as gnugo
GNUGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot", "gnugo-3.8", "gnugo.exe")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_board(board):
    size = board.get_size()
    
    def get_coord_letter(index):
        
        if index < 8:
            return chr(65 + index)
        else:
            
            return chr(66 + index) 
        
    print("   ", end="")
    for i in range(size):
        letter = get_coord_letter(i)
        print(f"{letter:2}", end="")
    print()
    
    for y in range(size):
        print(f"{y+1:2} ", end="")
        
        for x in range(size):
            color = board.get_color(x, y)
            if color == go.Color.Black:
                print("○", end=" ")
            elif color == go.Color.White:
                print("●", end=" ")
            else:
                if (size == 19 and 
                    ((x in [3,9,15] and y in [3,9,15]) or
                     (x in [3,9,15] and y in [3,15]) or
                     (y in [3,9,15] and x in [3,15]))):
                    print("·", end=" ")
                else:
                    print(".", end=" ")
        print()

def get_player_move(player_name, move_number):
    while True:
        try:
            print(f"\n{player_name}, ваш ход (номер хода: {move_number})")
            print("Введите координаты (например, D4) или 'pass' для паса, 'undo' для отмены последнего хода: ", end="")
            move_input = input().strip().lower()
            
            if move_input == 'pass':
                return {'is_pass': True, 'x': -1, 'y': -1}
            elif move_input == 'undo':
                return {'is_pass': False, 'undo': True}
            elif move_input == 'quit':
                return {'is_pass': False, 'quit': True}
            
            
            letter = move_input[0].upper()
            if letter >= 'I':
                x = ord(letter) - ord('A') - 1
            else:
                x = ord(letter) - ord('A')
            
            y = int(move_input[1:]) - 1
            
            if x < 0 or x >= 19 or y < 0 or y >= 19:
                print("❌ Координаты вне доски! Попробуйте снова.")
                continue
                
            return {'is_pass': False, 'x': x, 'y': y}
            
        except (ValueError, IndexError):
            print("❌ Неверный формат! Используйте формат: буква + число (например, D4)")
        except KeyboardInterrupt:
            print("\n\n👋 Игра прервана игроком.")
            return {'is_pass': False, 'quit': True}

def play_game():
    clear_screen()
    print("=" * 50)
    print("         ДОБРО ПОЖАЛОВАТЬ В ИГРУ ГО")
    print("=" * 50)
    print("\n📋 Правила игры:")
    print("  • Черные ходят первыми")
    print("  • Введите координаты в формате 'D4'")
    print("  • Введите 'pass' для пропуска хода")
    print("  • Введите 'undo' для отмены последнего хода")
    print("  • Введите 'quit' для выхода из игры")
    print("  • Игра заканчивается после двух пасов подряд\n")
    
    while True:
        try:
            size = int(input("Выберите размер доски (9, 13, 19): "))
            if size in [9, 13, 19]:
                break
            else:
                print("❌ Размер должен быть 9, 13 или 19")
        except ValueError:
            print("❌ Введите число")
    
    print("\n📝 Введите имена игроков:")
    black_name = input("Черные (ходят первыми): ").strip() or "Игрок 1"
    white_name = input("Белые: ").strip() or "Игрок 2"
    
    game = go.Game(size)
    board = game.get_board()
    
    game_active = True
    
    while game_active:
        clear_screen()
        legal_moves = game.get_legal_moves()################################
        current_player = game.get_current_player()
        if current_player == go.Color.Black:
            player_name = black_name
            player_symbol = "● Черные"
        else:
            player_name = white_name
            player_symbol = "○ Белые"
        
        print("=" * 60)
        print(f"           ИГРА ГО ({size}x{size})")
        print("=" * 60)
        print(f"📊 Ход номер: {game.get_move_number()}")
        print(f"🎮 Текущий игрок: {player_name} ({player_symbol})")
        print(f"🔄 Пасов подряд: {game.get_passes()}")
        print("-" * 60)
        
        print_board(board)
        print_board(legal_moves)#########################################1
        
        if game.is_game_over():
            print("\n" + "=" * 60)
            print("🏆 ИГРА ОКОНЧЕНА!")
            print("=" * 60)
    
            print("\n🔍 Анализ позиции с помощью GNU Go...")
    
            sgf_content = game.get_sgf()
            # print(f"📄 SGF для анализа: {sgf_content}")
    
            print(f"🔍 Проверка пути: {GNUGO_PATH}")
            print(f"📁 Файл существует: {os.path.exists(GNUGO_PATH)}")
    
            if os.path.exists(GNUGO_PATH) and gnugo.check_gnugo_available(GNUGO_PATH):
                print(f"✅ GNU Go найден и работает")
        
                analyzer = gnugo.GnuGoAnalyzer(gnugo_path=GNUGO_PATH)
        
                try:
                    print("🔄 Запуск анализа...")
                    result = analyzer.analyze_sgf(sgf_content, size)
            
                    if result:
                        print("\n" + "=" * 60)
                        print("📊 РЕЗУЛЬТАТ ПАРТИИ")
                        print("=" * 60)
                        print(f"🏆 Победитель: {result['winner']}")
                        print(f"📈 Счет: {result['full_result']}")
                        if 'margin' in result:
                            print(f"🎯 Разница: {result['margin']} очков")
                    else:
                        print("❌ Не удалось получить результат от GNU Go")
                
                except Exception as e:
                    print(f"❌ Ошибка при анализе: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    analyzer.cleanup()
            else:
                print(f"❌ GNU Go не доступен по пути: {GNUGO_PATH}")
                print("Проверьте наличие файла gnugo.exe в указанной папке")
    
            print("\n" + "=" * 60)
            break
        
        move = get_player_move(f"{player_name} ({player_symbol})", game.get_move_number())
        
        if move.get('quit'):
            print("\n👋 Спасибо за игру!")
            game_active = False
            break
        
        if move.get('undo'):
            if game.undo_last_move():
                print("\n↩️ Последний ход отменен!")
                if game.get_passes() > 0:
                    pass
                time.sleep(1)
            else:
                print("\n❌ Нельзя отменить ход!")
                time.sleep(1)
            continue
        
        try:
            if move['is_pass']:
                game.make_move(-1, -1, True)
                print(f"\n⏸️ {player_name} сделал пас")
                if game.get_passes() >= 2:
                    print("🎯 Два паса подряд - игра окончена!")
                time.sleep(1)
            else:
                game.make_move(move['x'], move['y'], False)
                print(f"\n✅ {player_name} сходил в {chr(65 + move['x'])}{move['y'] + 1}")
                time.sleep(0.5)
                
        except Exception as e:
            print(f"\n❌ Ошибка при ходе: {e}")
            print("Попробуйте снова.")
            time.sleep(1)
    
    if input("\n💾 Сохранить игру в SGF файл? (y/n): ").lower() == 'y':
        filename = f"go_game_{time.strftime('%Y%m%d_%H%M%S')}.sgf"
        if game.save_game(filename):
            print(f"✅ Игра сохранена в {filename}")
        else:
            print("❌ Ошибка при сохранении")
        
        print("\n📄 SGF содержимое:")
        print(game.get_sgf())
    
    print("\n👋 До свидания!")

def test_basic_moves():
    """Простая демонстрация игры"""
    print("🧪 Тестовый режим: несколько ходов")
    game = go.Game(9)
    board = game.get_board()
    
    moves = [(3, 3), (15, 15), (16, 15), (3, 4)]
    
    for i, (x, y) in enumerate(moves):
        if i % 2 == 0:
            print(f"\nХод черных: {chr(65 + x)}{y+1}")
        else:
            print(f"Ход белых: {chr(65 + x)}{y+1}")
        
        game.make_move(x, y, False)
        print_board(board)
        time.sleep(1)
    
    print("\n📄 SGF результат:")
    print(game.get_sgf())

if __name__ == "__main__":
    print("\n🎮 ВЫБЕРИТЕ РЕЖИМ:")
    print("1. Игра двух игроков")
    print("2. Демонстрация (тестовые ходы)")
    print("3. Выход")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        play_game()
    elif choice == '2':
        test_basic_moves()
    else:
        print("До свидания!")