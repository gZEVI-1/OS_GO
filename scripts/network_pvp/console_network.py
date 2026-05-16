"""
OS-GO Network PvP Console
"""
import asyncio
import argparse
import os
import sys
from typing import Optional
from output_interface import MessageData

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

try:
    from console_back import clear_screen, get_stone_symbol, is_hoshi_point, print_board as base_print_board, show_help
except ImportError:
    def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
    def get_stone_symbol(c, h): return "●" if c == 1 else ("○" if c == 2 else "+")
    def is_hoshi_point(x, y, s): return False
    def show_help(): print("Координаты: A1-T19 (без I)")

from client import NetworkClient, ConnectionState, GameState
from protocol import Message, RoomInfo
import go_engine as go


def add_katago_analysis_to_network_client(client: NetworkClient, on_analysis_complete=None):
    """
    Адаптирует KataGo-анализ для сетевого клиента.
    Полностью повторяет поведение add_katago_analysis_to_session().
    """
    original_on_game_over = client.on_game_over

    def wrapped_on_game_over(winner: str, result: str):
        try:
            from KataGoAnalyzer import KataGoAnalyzer, is_available
            if not is_available():
                print("\n⚠️ KataGo недоступен")
                if original_on_game_over:
                    original_on_game_over(winner, result)
                return

            sgf = client.get_sgf()
            if not sgf:
                print("\n⚠️ Нет данных партии для анализа")
                if original_on_game_over:
                    original_on_game_over(winner, result)
                return

            print("\n🔍 Анализ партии с KataGo...")
            analyzer = KataGoAnalyzer()
            if not analyzer.initialize():
                print("\n⚠️ Не удалось инициализировать KataGo")
                if original_on_game_over:
                    original_on_game_over(winner, result)
                return

            analysis_result = analyzer.analyze_sgf(sgf, client.board_size, client.komi)
            analyzer.cleanup()

            if analysis_result and analysis_result.success:
                if on_analysis_complete:
                    on_analysis_complete(analysis_result)
                else:
                    print("\n" + "=" * 60)
                    print("📊 АНАЛИЗ KATAGO")
                    print("=" * 60)
                    print(f"🏆 Победитель: {analysis_result.winner}")
                    print(f"📈 Результат: {analysis_result.full_result}")
                    print(f"⚫ Черные: {analysis_result.black_score:.1f}")
                    print(f"⚪ Белые: {analysis_result.white_score:.1f}")
                    if analysis_result.best_move:
                        print(f"💡 Лучший ход: {analysis_result.best_move}")
                    if analysis_result.top_moves:
                        print(f"🎯 Топ-5 ходов: {', '.join(analysis_result.top_moves[:5])}")
            else:
                print("\n⚠️ Анализ не выполнен")

        except Exception as e:
            print(f"\n❌ Ошибка анализа: {e}")

        if original_on_game_over:
            original_on_game_over(winner, result)

    client.on_game_over = wrapped_on_game_over

    
# === АСИНХРОННЫЙ ВВОД (не блокирует WebSocket) ===
async def ainput(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip())


def print_network_board(board_array: list, size: int, last_move: Optional[dict] = None):
    print("    ", end="")
    for i in range(size):
        letter = chr(ord('A') + i)
        if letter >= 'I': letter = chr(ord(letter) + 1)
        print(f"{letter:2} ", end="")
    print()
    for y in range(size):
        print(f"{y+1:2}  ", end="")
        for x in range(size):
            val = board_array[y][x] if y < len(board_array) and x < len(board_array[y]) else 0
            is_last = last_move and last_move.get("x") == x and last_move.get("y") == y
            symbol = get_stone_symbol(val, is_hoshi_point(x, y, size))
            print(f"[{symbol}] " if is_last else f" {symbol}  ", end="")
        print()

def print_network_state(client: NetworkClient):
    if not client.game_state: return
    state = client.game_state
    size = client.board_size
    print("=" * 60)
    print(f"           СЕТЕВАЯ ИГРА ГО ({size}x{size}) ")
    print("=" * 60)
    print(f"📊 Ход номер: {state.move_number} ")
    my_color = "○" if client.player_color == "black" else "●"
    turn_symbol = "○" if state.current_player == "black" else "●"
    is_my_turn = client.is_my_turn()
    print(f"🎮 Вы играете: {my_color} ({client.player_color}) ")
    print(f"🔄 Ход: {turn_symbol} {'(ВАШ!)' if is_my_turn else '(противник)'} ")
    print(f"⏭️ Пасов подряд: {state.passes} ")
    print("-" * 60)
    print_network_board(state.board_array, size, state.last_move)

def print_room_list(rooms: list[RoomInfo]):
    if not rooms:
        print("\n📭 Нет доступных комнат")
        return
    print("\n" + "=" * 60)
    print("           ДОСТУПНЫЕ КОМНАТЫ ")
    print("=" * 60)
    print(f"{'ID':<10} {'Название':<20} {'Хост':<15} {'Размер':<8} {'Игроки':<10} {'Статус'}")
    print("-" * 60)
    for room in rooms:
        lock = "🔒" if room.has_password else "  "
        players = f"{room.player_count}/{room.max_players}"
        print(f"{room.room_id:<10} {lock}{room.name:<18} {room.host_name:<15} {room.board_size}x{room.board_size:<3} {players:<10} {room.status}")

async def lobby_menu(client: NetworkClient) -> bool:
    rooms_received = asyncio.Event()
    available_rooms: list[RoomInfo] = []
    def on_room_list(rooms):
        nonlocal available_rooms
        available_rooms = rooms
        rooms_received.set()
    client.on_room_list = on_room_list
    
    try:
        await asyncio.wait_for(rooms_received.wait(), timeout=3.0)
    except asyncio.TimeoutError:
        print("⚠️ Таймаут ожидания списка комнат")

    while True:
        clear_screen()
        print("=" * 60)
        print("           ЛОББИ OS-GO ")
        print("=" * 60)
        print(f"👤 Игрок: {client.player_name} ")
        print(f"🌐 Сервер: {client.server_url} ")
        print()
        print_room_list(available_rooms)
        print("\nКоманды:")
        print("  create  <name> [size] [password] — создать комнату")
        print("  join  <room_id> [password]       — войти в комнату")
        print("  refresh                         — обновить список")
        print("  quit                            — выход\n")
        try:
            cmd = (await ainput(" > ")).split()
            if not cmd: continue
            action = cmd[0].lower()
            if action == "quit":
                await client.disconnect()
                return False
            elif action == "refresh":
                rooms_received.clear()
                await client._send(Message.lobby_ready())
                try:
                    await asyncio.wait_for(rooms_received.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    print("⚠️ Не удалось получить список")
                continue
            elif action == "create":
                name = cmd[1] if len(cmd) > 1 else f"Room_{client.player_name}"
                size = int(cmd[2]) if len(cmd) > 2 else 19
                password = cmd[3] if len(cmd) > 3 else None
                if size not in [9, 13, 19]:
                    print("❌ Размер должен быть 9, 13 или 19")
                    await ainput("Нажмите Enter...")
                    continue
                joined = asyncio.Event()
                def on_joined(rid, color): joined.set()
                client.on_room_joined = on_joined
                await client.create_room(name, size, password)
                try:
                    await asyncio.wait_for(joined.wait(), timeout=5.0)
                    print(f"✅ Комната создана! ID: {client.room_id}")
                    await asyncio.sleep(1)
                    return True
                except asyncio.TimeoutError: print("❌ Не удалось создать комнату")
            elif action == "join":
                if len(cmd) < 2:
                    print("❌ Укажите ID комнаты")
                    await ainput("Нажмите Enter...")
                    continue
                room_id = cmd[1]
                password = cmd[2] if len(cmd) > 2 else None
                joined = asyncio.Event()
                join_error = None
                def on_joined(rid, color): joined.set()
                def on_error(code, msg):
                    nonlocal join_error
                    join_error = f"[{code}] {msg}"
                    joined.set()
                client.on_room_joined = on_joined
                client.on_error = on_error
                await client.join_room(room_id, password)
                try:
                    await asyncio.wait_for(joined.wait(), timeout=5.0)
                    if join_error: print(f"❌ {join_error}")
                    else:
                        print(f"✅ Вошли в комнату! Играете за {client.player_color}")
                        await asyncio.sleep(1)
                        return True
                except asyncio.TimeoutError: print("❌ Таймаут подключения")
        except KeyboardInterrupt:
            await client.disconnect()
            return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            await ainput("Нажмите Enter...")

async def room_wait_menu(client: NetworkClient):
    players_updated = asyncio.Event()
    game_started = asyncio.Event()
    current_players = []

    def on_update(payload):
        nonlocal current_players
        current_players = payload.get("players", [])
        players_updated.set()
    client.on_room_update = on_update

    def on_start(_):
        game_started.set()
    client.on_game_started = on_start

    while True:
        clear_screen()
        print("=" * 60)
        print("           КОМНАТА ")
        print("=" * 60)
        print(f"🆔 ID комнаты: {client.room_id} ")
        print(f"🎨 Ваш цвет: {'○ Черные' if client.player_color == 'black' else '● Белые'} ")
        print("\nИгроки в комнате:")
        for p in current_players:
            ready = "✅" if p.get("is_ready") else "⏳"
            print(f"  {ready} {p.get('name', 'Unknown')} ({p.get('color', '?')})")
        print("\nКоманды: ready / unready / leave")

        # Ждём либо ввода, либо сигнала о начале игры от сервера
        input_task = asyncio.create_task(ainput(" > "))
        start_task = asyncio.create_task(game_started.wait())

        done, pending = await asyncio.wait(
            [input_task, start_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Отменяем висящую задачу
        # for task in pending:
        #     task.cancel()
        #     try:
        #         await task
        #     except asyncio.CancelledError:
        #         pass

        # Если игра началась — выходим сразу
        if start_task in done:
            return True

        # Иначе обрабатываем ввод
        try:
            cmd = input_task.result().lower().strip()
        except asyncio.CancelledError:
            continue

        if cmd == "ready":
            await client.set_ready(True)
            print("✅ Вы готовы!")
            await asyncio.sleep(0.5)
        elif cmd == "unready":
            await client.set_ready(False)
            print("⏳ Готовность отменена")
            await asyncio.sleep(0.5)
        elif cmd == "leave":
            await client.leave_room()
            return False

async def wait_for_state_update(client: NetworkClient):
    old_move = client.game_state.move_number if client.game_state else 0
    while client.state == ConnectionState.PLAYING:
        await asyncio.sleep(0.1)
        if client.game_state and client.game_state.move_number > old_move: return

async def game_loop(client: NetworkClient):
    from game_controller import NetworkController
    from unified_game_loop import run_unified_loop
    import output_interface as output

    if client.state != ConnectionState.PLAYING:
        game_started = asyncio.Event()
        def on_start(_): game_started.set()
        client.on_game_started = on_start
        try:
            await asyncio.wait_for(game_started.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            output.show_message("error", "Таймаут ожидания начала игры")
            return

    controller = NetworkController(client)

    # --- Подробный анализ KataGo (как в PvP/PvE) ---
    def on_katago_analysis(result):
        output.clear_screen()
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
        print("=" * 60)
        filepath = client.save_game()
        if filepath:
            print(f"\n💾 Партия сохранена: {filepath}")

    add_katago_analysis_to_network_client(client, on_katago_analysis)
    # ---

    await run_unified_loop(controller)


    

async def run_network_game():
    from output_interface import get_output_interface, OutputType, MessageData
    output = get_output_interface(OutputType.CONSOLE)
    parser = argparse.ArgumentParser(description="OS-GO Network PvP")
    parser.add_argument("--server", default="ws://localhost:8765")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()
    player_name = args.name or (await ainput("Введите ваше имя: ")) or "Player"
    client = NetworkClient(args.server, player_name)
    

    output.clear_screen()
    print("=" * 60)
    print("         ПОДКЛЮЧЕНИЕ К СЕРВЕРУ... ")
    print("=" * 60)
    print(f"🌐 Сервер: {args.server}")
    print(f"👤 Имя: {player_name}")
    if not await client.connect():
        output.show_message("error", "Не удалось подключиться к серверу")
        await ainput("\nНажмите Enter...")
        return
    output.show_message(MessageData("success", "Подключено!"))
    await asyncio.sleep(0.5)
    try:
        while True:
            in_room = await lobby_menu(client)
            if not in_room: 
                break
            game_ready = await room_wait_menu(client)
            if not game_ready: 
                continue
            await game_loop(client)
            client.state = ConnectionState.CONNECTED
            client.room_id = None
            client.game_state = None
    except Exception as e:
        output.show_message("error", f"Ошибка: {e}")
    finally:
        await client.disconnect()
        print("👋 Отключено от сервера")

if __name__ == "__main__":
    try: asyncio.run(run_network_game())
    except KeyboardInterrupt: print("\n👋 До свидания!")