# load_game_example.py

import go_engine as go
import os
import time
import re
from sgf_loader import SGFLoader
import config as cfg

def clear_screen():
    """Очистка экрана"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_board(board, size, show_coords=True):
    """Вывод доски с координатами"""
    def get_coord_letter(index):
        # Преобразование индекса в букву (пропуская I)
        if index < 8:
            return chr(65 + index)
        else:
            return chr(66 + index)
    
    # Верхняя строка с буквами
    if show_coords:
        print("   ", end="")
        for i in range(size):
            print(f"{get_coord_letter(i):2}", end="")
        print()
    
    # Вывод строк доски
    for y in range(size):
        if show_coords:
            print(f"{y+1:2} ", end="")
        else:
            print("  ", end="")
        
        for x in range(size):
            color = board.get_color(x, y)
            if color == go.Color.Black:
                print("●", end=" ")
            elif color == go.Color.White:
                print("○", end=" ")
            else:
                # Рисуем точки хошу (звёзды) для разных размеров
                if (size == 19 and 
                    ((x in [3, 9, 15] and y in [3, 9, 15]) or
                     (x in [3, 9, 15] and y in [3, 15]) or
                     (y in [3, 9, 15] and x in [3, 15]))):
                    print("·", end=" ")
                elif (size == 13 and 
                      ((x in [3, 6, 9] and y in [3, 6, 9]) or
                       (x in [3, 9] and y in [6]) or
                       (y in [3, 9] and x in [6]))):
                    print("·", end=" ")
                elif size == 9 and (x in [2, 4, 6] and y in [2, 4, 6]):
                    print("·", end=" ")
                else:
                    print(".", end=" ")
        print()

def print_legal_moves_board(legal_moves, size):
    """Вывод доски возможных ходов"""
    print("\n📋 Возможные ходы (● - можно сходить):")
    print("   ", end="")
    for i in range(size):
        if i < 8:
            print(f"{chr(65 + i):2}", end="")
        else:
            print(f"{chr(66 + i):2}", end="")
    print()
    
    for y in range(size):
        print(f"{y+1:2} ", end="")
        for x in range(size):
            color = legal_moves.get_color(x, y)
            if color == go.Color.Black:
                print("●", end=" ")
            else:
                print(".", end=" ")
        print()

def get_player_move(player_name, move_number, size, allow_undo=True, allow_save=True):
    """Получение хода от игрока"""
    while True:
        try:
            print(f"\n{player_name}, ваш ход (номер хода: {move_number})")
            print("Введите:")
            print("  • Координаты (например, D4)")
            print("  • 'pass' - пропустить ход")
            if allow_undo:
                print("  • 'undo' - отменить последний ход")
            if allow_save:
                print("  • 'save' - сохранить игру")
            print("  • 'quit' - выйти из игры")
            
            move_input = input("> ").strip().lower()
            
            if move_input == 'pass':
                return {'is_pass': True, 'x': -1, 'y': -1}
            elif move_input == 'undo' and allow_undo:
                return {'is_pass': False, 'undo': True}
            elif move_input == 'save' and allow_save:
                return {'is_pass': False, 'save': True}
            elif move_input == 'quit':
                return {'is_pass': False, 'quit': True}
            
            # Парсинг координат
            if len(move_input) < 2:
                print("❌ Неверный формат! Используйте букву и число (например, D4)")
                continue
            
            letter = move_input[0].upper()
            if letter >= 'I':
                x = ord(letter) - ord('A') - 1
            else:
                x = ord(letter) - ord('A')
            
            y = int(move_input[1:]) - 1
            
            if x < 0 or x >= size or y < 0 or y >= size:
                print(f"❌ Координаты вне доски {size}x{size}!")
                continue
                
            return {'is_pass': False, 'x': x, 'y': y}
            
        except (ValueError, IndexError):
            print("❌ Неверный формат! Используйте формат: буква + число (например, D4)")
        except KeyboardInterrupt:
            print("\n\n👋 Игра прервана.")
            return {'is_pass': False, 'quit': True}

def save_current_game(game, filename=None):
    """Сохранение текущей игры"""
    if filename is None:
        filename = cfg.get_sgf_path(game_mode="loaded")
    
    if game.save_game(filename):
        print(f"✅ Игра сохранена в {filename}")
        return True
    else:
        print(f"❌ Ошибка при сохранении в {filename}")
        return False

def continue_game_from_sgf():
    """Продолжить партию из SGF файла"""
    clear_screen()
    print("=" * 60)
    print("         ПРОДОЛЖИТЬ ПАРТИЮ ИЗ SGF")
    print("=" * 60)
    
    #доступные файлы
    saves_dir = cfg.get_saves_dir()
    sgf_files = []
#                      |      |       |
    #копаем директории V      V       V
    for mode_dir in ['pvp', 'pve', 'loaded']:
        full_path = os.path.join(saves_dir, mode_dir)
        if os.path.exists(full_path):
            for f in os.listdir(full_path):
                if f.endswith('.sgf'):
                    sgf_files.append(os.path.join(mode_dir, f))
    
    if sgf_files:
        print("\n📂 Доступные сохранения:")
        for i, f in enumerate(sgf_files, 1):
            print(f"  {i}. {f}")
        print(f"  {len(sgf_files) + 1}. Ввести путь вручную")
        
        try:
            choice = input(f"\nВыберите файл (1-{len(sgf_files) + 1}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(sgf_files):
                sgf_path = os.path.join(saves_dir, sgf_files[choice_num - 1])
            elif choice_num == len(sgf_files) + 1:
                sgf_path = input("Введите путь к SGF файлу: ").strip()
            else:
                print("❌ Неверный выбор")
                return
        except ValueError:
            sgf_path = input("Введите путь к SGF файлу: ").strip()
    else:
        sgf_path = input("Введите путь к SGF файлу: ").strip()
    
    if not os.path.exists(sgf_path):
        print(f"❌ Файл не найден: {sgf_path}")
        input("\nНажмите Enter для продолжения...")
        return
    
    try:
        #читаем
        with open(sgf_path, 'r', encoding='utf-8') as f:
            sgf_content = f.read()
        
        #размер
        size = SGFLoader.get_board_size(sgf_content)
        print(f"📏 Размер доски: {size}x{size}")
        
        #имена
        black_name, white_name = SGFLoader.get_player_names(sgf_content)
        print(f"👤 Игроки: {black_name} (Черные) vs {white_name} (Белые)")
        
        result = SGFLoader.get_result(sgf_content)
        if result:
            print(f"📊 Результат в файле: {result}")
        
        game = go.Game(size)
        
        if SGFLoader.load_from_string(sgf_content, game):
            move_count = game.get_move_number() - 1
            print(f"✅ Загружено {move_count} ходов")
            
            if game.is_game_over():
                print("\n🏁 Эта партия уже завершена!")
                print("Хотите посмотреть финальную позицию и подсчитать очки?")
                choice = input("(y/n): ").strip().lower()
                if choice == 'y':
                    show_final_position(game, size, black_name, white_name)
                return
            
            print(f"\n🎮 Следующий ход: {'Черные' if game.get_current_player() == go.Color.Black else 'Белые'}")
            
            choice = input("\nПродолжить игру? (y/n): ").strip().lower()
            if choice == 'y':
                play_continued_game(game, size, black_name, white_name, sgf_path)
            else:
                print("👋 До свидания!")
        else:
            print("❌ Не удалось загрузить партию")
            
    except FileNotFoundError:
        print(f"❌ Файл не найден: {sgf_path}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nНажмите Enter для продолжения...")

def play_continued_game(game, size, black_name, white_name, original_sgf_path):
    """Продолжить игру с загруженной позиции"""
    game_active = True
    auto_save_counter = 0
    
    print("\n" + "=" * 60)
    print("         ПРОДОЛЖЕНИЕ ПАРТИИ")
    print("=" * 60)
    print("💡 Советы:")
    print("  • Введите 'undo' для отмены последнего хода")
    print("  • Введите 'save' для сохранения игры")
    print("  • Введите 'score' для подсчёта текущих очков")
    print("=" * 60)
    
    while game_active:
        clear_screen()
        
        current_player = game.get_current_player()
        move_number = game.get_move_number()
        
        if current_player == go.Color.Black:
            player_name = black_name
            player_symbol = "● Черные"
        else:
            player_name = white_name
            player_symbol = "○ Белые"
        
        print("=" * 60)
        print(f"           ИГРА ГО ({size}x{size})")
        print("=" * 60)
        print(f"📊 Ход номер: {move_number}")
        print(f"🎮 Текущий игрок: {player_name} ({player_symbol})")
        print(f"🔄 Пасов подряд: {game.get_passes()}")
        print("-" * 60)
        
        print_board(game.get_board(), size)
        
        if game.is_game_over():
            print("\n" + "=" * 60)
            print("🏆 ИГРА ОКОНЧЕНА!")
            print("=" * 60)
            
            calculate_and_show_score(game, size, black_name, white_name)
            break
        
        move = get_player_move(player_name, move_number, size, 
                               allow_undo=True, allow_save=True)
        
        if move.get('quit'):
            save_before_quit = input("\nСохранить игру перед выходом? (y/n): ").strip().lower()
            if save_before_quit == 'y':
                save_current_game(game)
            print("\n👋 Спасибо за игру!")
            game_active = False
            break
        
        if move.get('undo'):
            if game.undo_last_move():
                print("\n↩️ Последний ход отменен!")
                time.sleep(1)
            else:
                print("\n❌ Нельзя отменить ход!")
                time.sleep(1)
            continue
        
        if move.get('save'):
            save_current_game(game)
            input("\nНажмите Enter для продолжения...")
            continue
        
        try:
            if move['is_pass']:
                success = game.make_move(-1, -1, True)
                if success:
                    print(f"\n⏸️ {player_name} сделал пас")
                    if game.get_passes() >= 2:
                        print("🎯 Два паса подряд - игра окончена!")
                    time.sleep(1)
                else:
                    print("\n❌ Нельзя сделать пас? (ошибка)")
                    time.sleep(1)
            else:
                success = game.make_move(move['x'], move['y'], False)
                if success:
                    x, y = move['x'], move['y']
                    if x < 8:
                        letter = chr(65 + x)
                    else:
                        letter = chr(66 + x)
                    print(f"\n✅ {player_name} сходил в {letter}{y + 1}")
                    time.sleep(0.5)
                else:
                    print("\n❌ Неверный ход! Попробуйте снова.")
                    time.sleep(1)
                    continue
            
           
                save_current_game(game)
                
        except Exception as e:
            print(f"\n❌ Ошибка при ходе: {e}")
            print("Попробуйте снова.")
            time.sleep(1)
    
    if game_active == False and not game.is_game_over():
        save_choice = input("\nСохранить игру перед выходом? (y/n): ").strip().lower()
        if save_choice == 'y':
            save_current_game(game)

def calculate_and_show_score(game, size, black_name, white_name):
    """Подсчёт и вывод очков с помощью GNU Go"""
    print("\n🔍 Подсчёт очков...")
    
    sgf_content = game.get_sgf()
    
    try:
        import scripts2k.GnuGo_Analyzer as gnugo
        
        gnugo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot", "gnugo-3.8", "gnugo.exe")
        
        if gnugo_path and os.path.exists(gnugo_path):
            analyzer = gnugo.GnuGoAnalyzer(gnugo_path=gnugo_path)
            
            try:
                result = analyzer.analyze_sgf(sgf_content, size)
                
                if result:
                    print("\n" + "=" * 60)
                    print("📊 ТЕКУЩАЯ ОЦЕНКА ПОЗИЦИИ")
                    print("=" * 60)
                    print(f"🏆 Лидирует: {result['winner']}")
                    print(f"📈 Счёт: {result['full_result']}")
                    
                    if 'margin' in result:
                        if result['winner_color'] == 'B':
                            print(f"🎯 Преимущество чёрных: {result['margin']} очков (с учётом коми 6.5)")
                        else:
                            print(f"🎯 Преимущество белых: {result['margin']} очков")
                else:
                    print("❌ Не удалось получить оценку позиции")
                    
            finally:
                analyzer.cleanup()
        else:
            print("⚠️ GNU Go не доступен для подсчёта очков")
            print("Установите GNU Go для получения оценки позиции")
            
    except ImportError:
        print("⚠️ Модуль GnuGo_Analyzer не найден")
    except Exception as e:
        print(f"❌ Ошибка при подсчёте: {e}")

def show_final_position(game, size, black_name, white_name):
    """Показать финальную позицию завершённой партии"""
    clear_screen()
    
    print("=" * 60)
    print("         ФИНАЛЬНАЯ ПОЗИЦИЯ")
    print("=" * 60)
    
    print_board(game.get_board(), size)
    
    calculate_and_show_score(game, size, black_name, white_name)
    
    print("\n" + "=" * 60)
    print("Доступные действия:")
    print("1. Сохранить SGF")
    print("2. Назад")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        save_current_game(game)
    else:
        return

def calculate_score_from_sgf():
    """Подсчёт очков из SGF файла (без продолжения игры)"""
    clear_screen()
    print("=" * 60)
    print("         ПОДСЧЁТ ОЧКОВ ИЗ SGF")
    print("=" * 60)
    
    sgf_path = input("Введите путь к SGF файлу: ").strip()
    
    if not os.path.exists(sgf_path):
        print(f"❌ Файл не найден: {sgf_path}")
        input("\nНажмите Enter для продолжения...")
        return
    
    try:
        with open(sgf_path, 'r', encoding='utf-8') as f:
            sgf_content = f.read()
        
        size = SGFLoader.get_board_size(sgf_content)
        black_name, white_name = SGFLoader.get_player_names(sgf_content)
        
        print(f"\n📏 Размер доски: {size}x{size}")
        print(f"👤 Игроки: {black_name} (Черные) vs {white_name} (Белые)")
        
        game = go.Game(size)
        SGFLoader.load_from_string(sgf_content, game)
        
        print("\n📊 ФИНАЛЬНАЯ ПОЗИЦИЯ:")
        print_board(game.get_board(), size)
        
        calculate_and_show_score(game, size, black_name, white_name)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nНажмите Enter для продолжения...")

def show_sgf_info():
    """Показать информацию о SGF файле"""
    clear_screen()
    print("=" * 60)
    print("         ИНФОРМАЦИЯ О SGF")
    print("=" * 60)
    
    sgf_path = input("Введите путь к SGF файлу: ").strip()
    
    if not os.path.exists(sgf_path):
        print(f"❌ Файл не найден: {sgf_path}")
        input("\nНажмите Enter для продолжения...")
        return
    
    try:
        with open(sgf_path, 'r', encoding='utf-8') as f:
            sgf_content = f.read()
        
        print("\n" + "=" * 60)
        print("📋 ИНФОРМАЦИЯ О ПАРТИИ")
        print("=" * 60)
        
        size = SGFLoader.get_board_size(sgf_content)
        black, white = SGFLoader.get_player_names(sgf_content)
        result = SGFLoader.get_result(sgf_content)
        
        print(f"📏 Размер доски: {size}x{size}")
        print(f"👤 Чёрные: {black}")
        print(f"👤 Белые: {white}")
        print(f"🏆 Результат: {result if result else 'Не указан'}")
        
        moves = SGFLoader.parse_moves(sgf_content)
        print(f"🎯 Количество ходов: {len(moves)}")
        
        passes = sum(1 for m in moves if m['is_pass'])
        print(f"⏸️ Пасов: {passes}")
        
        is_completed = passes >= 2 or result is not None
        print(f"🏁 Партия завершена: {'Да' if is_completed else 'Нет'}")
        
        if moves:
            print("\n📜 Первые 5 ходов:")
            for i, move in enumerate(moves[:5], 1):
                if move['is_pass']:
                    print(f"  {i}. {'Черные' if move['color'] == go.Color.Black else 'Белые'} - пас")
                else:
                    letter = chr(65 + move['x'] + (1 if move['x'] >= 8 else 0))
                    print(f"  {i}. {'Черные' if move['color'] == go.Color.Black else 'Белые'} - {letter}{move['y'] + 1}")
            
            if len(moves) > 5:
                print("\n📜 Последние 5 ходов:")
                for i, move in enumerate(moves[-5:], len(moves) - 4):
                    if move['is_pass']:
                        print(f"  {i}. {'Черные' if move['color'] == go.Color.Black else 'Белые'} - пас")
                    else:
                        letter = chr(65 + move['x'] + (1 if move['x'] >= 8 else 0))
                        print(f"  {i}. {'Черные' if move['color'] == go.Color.Black else 'Белые'} - {letter}{move['y'] + 1}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    input("\nНажмите Enter для продолжения...")

def main():
    """Главное меню"""
    while True:
        clear_screen()
        print("\n" + "=" * 60)
        print("         ЗАГРУЗКА SGF ФАЙЛОВ")
        print("=" * 60)
        print("\n📁 Доступные действия:")
        print("  1. Продолжить партию из SGF")
        print("  2. Подсчитать очки из SGF")
        print("  3. Информация о SGF файле")
        print("  4. Назад в главное меню")
        
        choice = input("\n👉 Ваш выбор (1-4): ").strip()
        
        if choice == '1':
            continue_game_from_sgf()
        elif choice == '2':
            calculate_score_from_sgf()
        elif choice == '3':
            show_sgf_info()
        elif choice == '4':
            print("\n👋 Возврат в главное меню...")
            break
        else:
            print("❌ Неверный выбор!")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Программа завершена.")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")