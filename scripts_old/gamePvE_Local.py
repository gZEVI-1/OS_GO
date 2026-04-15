import go_engine as go
import os
import time
import subprocess
import scripts2k.GnuGo_Analyzer as gnugo
import config as cfg

GNUGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot", "gnugo-3.8", "gnugo.exe")

#процесс
gnugo_process = None
#почистить экран
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
#вывод доски
def print_board(board):
    size = board.get_size()
    #это связано с отсутствием буквы I
    def get_coord_letter(index):
        if index < 8:
            return chr(65 + index)
        else:
            return chr(66 + index)
    
    print("   ", end="")
    for i in range(size):
        print(f"{get_coord_letter(i):2}", end="")
    print()
    #вывод 
    for y in range(size):
        print(f"{y+1:2} ", end="")
        
        for x in range(size):
            color = board.get_color(x, y)
            if color == go.Color.Black:
                print("○", end=" ")
            elif color == go.Color.White:
                print("●", end=" ")
            else:
                if size == 19 and ((x in [3,9,15] and y in [3,9,15]) or
                                   (x in [3,9,15] and y in [3,15]) or
                                   (y in [3,9,15] and x in [3,15])):
                    print("·", end=" ")
                elif size == 13 and ((x in [3,6,9] and y in [3,6,9]) or
                                     (x in [3,9] and y in [6]) or
                                     (y in [3,9] and x in [6])):
                    print("·", end=" ")
                elif size == 9 and (x in [2,4,6] and y in [2,4,6]):
                    print("·", end=" ")
                else:
                    print(".", end=" ")
        print()

def get_player_move(player_name, move_number, size):
    while True:
        try:
            print(f"\n{player_name}, ваш ход (номер хода: {move_number})")
            print("Введите координаты (например, D4) или 'pass': ", end="")
            move_input = input().strip().lower()
            
            if move_input == 'pass':
                return {'is_pass': True, 'x': -1, 'y': -1}
            elif move_input == 'quit':
                return {'is_pass': False, 'quit': True}
            
            letter = move_input[0].upper()
            
            if letter == 'I':
                print("❌ Буква 'I' не используется! Используйте H или J.")
                continue
            
            if letter <= 'H':
                x = ord(letter) - ord('A')
            else:
                x = ord(letter) - ord('A') - 1
            
            y = int(move_input[1:]) - 1
            
            if x < 0 or x >= size or y < 0 or y >= size:
                print(f"❌ Координаты вне доски {size}x{size}!")
                continue
                
            return {'is_pass': False, 'x': x, 'y': y}
            
        except (ValueError, IndexError):
            print("❌ Неверный формат! Используйте формат: буква + число")
        except KeyboardInterrupt:
            print("\n\n👋 Игра прервана.")
            return {'is_pass': False, 'quit': True}


def start_gnugo(board_size):
    """Запускает GNU Go и инициализирует доску"""
    global gnugo_process
    
    print("🔄 Запуск GNU Go...")
    #запуск процесса
    gnugo_process = subprocess.Popen(
        [GNUGO_PATH, "--mode", "gtp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    
    #начальные параметры
    gtp_command(f"boardsize {board_size}")
    gtp_command("clear_board")
    gtp_command("komi 6.5")
    
    print("✅ GNU Go готов к работе")


def gtp_command(cmd: str) -> str:
    """Отправляет команду в GNU Go и возвращает ответ"""
    global gnugo_process
    
    if gnugo_process is None:
        raise Exception("GNU Go не запущен")
    
    # Отправляем команду
    gnugo_process.stdin.write(cmd + "\n")
    gnugo_process.stdin.flush()
    
    # Читаем ответ
    lines = []
    while True:
        line = gnugo_process.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        lines.append(line)
        if line == "":
            break
    
    return "\n".join(lines)


def gnugo_play_move(color, x, y, is_pass=False):
    """Отправляет ход в GNU Go"""
    if is_pass:
        cmd = f"play {color} pass"
    else:
        #в GTP
        if x < 8:
            letter = chr(65 + x)
        else:
            letter = chr(66 + x)
        gtp_y = y + 1
        cmd = f"play {color} {letter}{gtp_y}"
    
    response = gtp_command(cmd)
    return response


def gnugo_get_move(color):
    """Получает ход от GNU Go"""
    cmd = f"genmove {color}"
    response = gtp_command(cmd)
    
    #парсинг хода от гнуго
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('='):
            move_str = line[1:].strip()
            
            if move_str == 'pass':
                return {'is_pass': True, 'x': -1, 'y': -1}
            
            if move_str and len(move_str) >= 2:
                letter = move_str[0]
                try:
                    y = int(move_str[1:]) - 1
                    
                    if letter <= 'H':
                        x = ord(letter) - ord('A')
                    else:
                        x = ord(letter) - ord('A') - 1
                    
                    return {'is_pass': False, 'x': x, 'y': y}
                except:
                    pass
    
    return {'is_pass': True, 'x': -1, 'y': -1}


def gnugo_showboard():
    """Показывает доску GNU Go (для отладки)"""
    return gtp_command("showboard")


def stop_gnugo():
    """Завершает работу GNU Go"""
    global gnugo_process
    
    if gnugo_process:
        try:
            gtp_command("quit")
        except:
            pass
        
        gnugo_process.terminate()
        gnugo_process = None
        print("🛑 GNU Go остановлен")


def play_vs_gnugo():
    clear_screen()
    print("=" * 60)
    print("         ИГРА ПРОТИВ GNU GO")
    print("=" * 60)
    
    #проверка
    if not os.path.exists(GNUGO_PATH):
        print(f"\n❌ GNU Go не найден по пути: {GNUGO_PATH}")
        print("Пожалуйста, проверьте путь к GNU Go")
        input("\nНажмите Enter для возврата...")
        return
    
    print("\n📋 Правила игры:")
    print("  • Вы играете против GNU Go")
    print("  • Введите координаты в формате 'D4'")
    print("  • Введите 'pass' для пропуска хода")
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
    
    # Выбор цвета
    print("\n🎨 Выберите цвет:")
    print("1. Играть черными (первые)")
    print("2. Играть белыми (вторые)")
    
    while True:
        choice = input("Ваш выбор (1-2): ").strip()
        if choice == '1':
            player_color = go.Color.Black
            gnugo_color = go.Color.White
            player_name = "Вы (Черные)"
            gnugo_name = "GNU Go (Белые)"
            player_gtp = 'B'
            gnugo_gtp = 'W'
            break
        elif choice == '2':
            player_color = go.Color.White
            gnugo_color = go.Color.Black
            player_name = "Вы (Белые)"
            gnugo_name = "GNU Go (Черные)"
            player_gtp = 'W'
            gnugo_gtp = 'B'
            break
        else:
            print("❌ Выберите 1 или 2")
    
    print(f"\n📝 Вы играете за {player_name}")
    print(f"🤖 Противник: {gnugo_name}")
    
    #запуск гнуго
    try:
        start_gnugo(size)
    except Exception as e:
        print(f"❌ Ошибка при запуске GNU Go: {e}")
        input("\nНажмите Enter для возврата...")
        return
    
    game = go.Game(size)
    board = game.get_board()
    
    game_active = True
    
    if player_color == go.Color.White:
        print(f"\n🤔 {gnugo_name} делает первый ход...")
        time.sleep(1)
        
        gnugo_move = gnugo_get_move(gnugo_gtp)
        
        try:
            if gnugo_move['is_pass']:
                game.make_move(-1, -1, True)
                print(f"\n⏸️ {gnugo_name} сделал пас")
            else:
                game.make_move(gnugo_move['x'], gnugo_move['y'], False)
                x, y = gnugo_move['x'], gnugo_move['y']
                letter = chr(65 + x + (1 if x >= 8 else 0))
                print(f"\n🤖 {gnugo_name} сходил в {letter}{y + 1}")
            time.sleep(1.5)
        except Exception as e:
            print(f"\n❌ Ошибка при ходе GNU Go: {e}")
    #процесс пошел
    while game_active:
        clear_screen()
        
        current_player = game.get_current_player()
        
        print("=" * 60)
        print(f"           ИГРА ПРОТИВ GNU GO ({size}x{size})")
        print("=" * 60)
        print(f"📊 Ход номер: {game.get_move_number()}")
        print(f"🎮 Текущий игрок: ", end="")
        if current_player == go.Color.Black:
            print("● Черные")
        else:
            print("○ Белые")
        print(f"🔄 Пасов подряд: {game.get_passes()}")
        print("-" * 60)
        
        print_board(board)
        
        #конец игры
        if game.is_game_over():
            print("\n" + "=" * 60)
            print("🏆 ИГРА ОКОНЧЕНА!")
            print("=" * 60)
            
            #считать очки
            print("\n🔍 Подсчет очков с помощью GNU Go...")
            
            sgf_content = game.get_sgf()
            
            if os.path.exists(GNUGO_PATH):
                analyzer = gnugo.GnuGoAnalyzer(gnugo_path=GNUGO_PATH)
                
                try:
                    result = analyzer.analyze_sgf(sgf_content, size)
                    
                    if result:
                        print("\n" + "=" * 60)
                        print("📊 РЕЗУЛЬТАТ ПАРТИИ")
                        print("=" * 60)
                        print(f"🏆 Победитель: {result['winner']}")
                        print(f"📈 Счет: {result['full_result']}")
                        
                        if result['winner'] == "Черные":
                            if player_color == go.Color.Black:
                                print("\n🎉 ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!")
                            else:
                                print("\n🤖 GNU Go победил")
                        else:
                            if player_color == go.Color.White:
                                print("\n🎉 ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!")
                            else:
                                print("\n🤖 GNU Go победил")
                    else:
                        print("❌ Не удалось получить результат")
                        
                finally:
                    analyzer.cleanup()
            else:
                print("❌ GNU Go не доступен для подсчета")
            
            print("\n" + "=" * 60)
            break
        
        if current_player == player_color:
            move = get_player_move(player_name, game.get_move_number(), size)
            
            if move.get('quit'):
                print("\n👋 Спасибо за игру!")
                game_active = False
                break
            
            try:
                if move['is_pass']:
                    game.make_move(-1, -1, True)
                    gnugo_play_move(player_gtp, -1, -1, True)
                    print(f"\n⏸️ Вы сделали пас")
                else:
                    game.make_move(move['x'], move['y'], False)
                    gnugo_play_move(player_gtp, move['x'], move['y'], False)
                    x, y = move['x'], move['y']
                    letter = chr(65 + x + (1 if x >= 8 else 0))
                    print(f"\n✅ Вы сходили в {letter}{y + 1}")
                time.sleep(1)
                
            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                print("Попробуйте другой ход.")
                time.sleep(1)
                continue
        
        else:
            print(f"\n🤔 {gnugo_name} думает...")
            
            gnugo_move = gnugo_get_move(gnugo_gtp)
            
            try:
                if gnugo_move['is_pass']:
                    game.make_move(-1, -1, True)
                    print(f"\n⏸️ {gnugo_name} сделал пас")
                else:
                    game.make_move(gnugo_move['x'], gnugo_move['y'], False)
                    x, y = gnugo_move['x'], gnugo_move['y']
                    letter = chr(65 + x + (1 if x >= 8 else 0))
                    print(f"\n🤖 {gnugo_name} сходил в {letter}{y + 1}")
                    
                time.sleep(1.5)
                
            except Exception as e:
                print(f"\n❌ Ошибка при ходе GNU Go: {e}")
                print("⚠️ GNU Go делает пас")
                game.make_move(-1, -1, True)
                time.sleep(1)
    
    #конец игры
    stop_gnugo()
    
    #в файл sgf
    
    filename = cfg.get_sgf_path(game_mode="pve")
    if game.save_game(filename):
        print(f"✅ Игра сохранена в {filename}")
    
    print("\n👋 До свидания!")


def test_gnugo_connection():#тестовый запуск на проверку работы гнуго
    """Тест соединения с GNU Go"""
    print("🧪 Тест соединения с GNU Go")
    print("=" * 50)
    
    if not os.path.exists(GNUGO_PATH):
        print(f"❌ GNU Go не найден по пути: {GNUGO_PATH}")
        return
    
    try:
        start_gnugo(9)
        
        print("✅ boardsize 9")
        print("✅ clear_board")
        print("✅ komi 6.5")
        
        # Получаем ход
        print("\n🔄 Получение хода черных...")
        move = gnugo_get_move('B')
        if move['is_pass']:
            print("GNU Go сделал пас")
        else:
            x, y = move['x'], move['y']
            letter = chr(65 + x + (1 if x >= 8 else 0))
            print(f"GNU Go сходил в {letter}{y + 1}")
        
        print("\n🔄 Доска GNU Go:")
        print(gnugo_showboard())
        
        stop_gnugo()
        print("\n✅ Тест завершен")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        stop_gnugo()


if __name__ == "__main__":
    print("\n🎮 РЕЖИМ ИГРЫ ПРОТИВ GNU GO")
    print("=" * 50)
    print("1. Начать игру")
    print("2. Тест соединения с GNU Go")
    print("3. Назад")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        play_vs_gnugo()
    elif choice == '2':
        test_gnugo_connection()
    else:
        print("Возврат в главное меню")