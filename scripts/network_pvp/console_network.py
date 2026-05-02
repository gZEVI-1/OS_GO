"""
OS-GO Network PvP Console

Запуск:
python console_network.py --server ws://192.168.1.1:8765 --name Player2


"""
import asyncio
import argparse
import os
import sys
from typing import Optional

# Исправляем пути
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

try:
    from console_back import clear_screen, get_stone_symbol, is_hoshi_point, print_board as base_print_board, show_help
except ImportError:
    # Fallback если console_back нет в пути
    def clear_screen(): os.system('cls' if os.name == 'nt' else 'clear')
    def get_stone_symbol(c, h): return "●" if c == 1 else ("○" if c == 2 else "+")
    def is_hoshi_point(x, y, s): return False
    def show_help(): print("Координаты: A1-T19 (без I)")

from client import NetworkClient, ConnectionState, GameState
from protocol import Message, RoomInfo
import go_engine as go

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
    await client._send(Message.connect(client.player_name))
    try: await asyncio.wait_for(rooms_received.wait(), timeout=2.0)
    except asyncio.TimeoutError: pass

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
            cmd = input(" > ").strip().split()
            if not cmd: continue
            action = cmd[0].lower()
            if action == "quit":
                await client.disconnect()
                return False
            elif action == "refresh":
                rooms_received.clear()
                await client.disconnect()
                if await client.connect():
                    try: await asyncio.wait_for(rooms_received.wait(), timeout=3.0)
                    except asyncio.TimeoutError: print("⚠️ Не удалось получить список")
                continue
            elif action == "create":
                name = cmd[1] if len(cmd) > 1 else f"Room_{client.player_name}"
                size = int(cmd[2]) if len(cmd) > 2 else 19
                password = cmd[3] if len(cmd) > 3 else None
                if size not in [9, 13, 19]:
                    print("❌ Размер должен быть 9, 13 или 19")
                    input("Нажмите Enter...")
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
                    input("Нажмите Enter...")
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
            input("Нажмите Enter...")

async def room_wait_menu(client: NetworkClient):
    players_updated = asyncio.Event()
    current_players = []
    def on_update(payload):
        nonlocal current_players
        current_players = payload.get("players", [])
        players_updated.set()
    client.on_room_update = on_update
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
        try:
            cmd = input(" > ").strip().lower()
            if cmd == "ready":
                await client.set_ready(True)
                print("✅ Вы готовы!")
            elif cmd == "unready":
                await client.set_ready(False)
                print("⏳ Готовность отменена")
            elif cmd == "leave":
                await client.leave_room()
                return False
            if client.state == ConnectionState.PLAYING: return True
        except KeyboardInterrupt:
            await client.leave_room()
            return False

async def wait_for_state_update(client: NetworkClient):
    old_move = client.game_state.move_number if client.game_state else 0
    while client.state == ConnectionState.PLAYING:
        await asyncio.sleep(0.1)
        if client.game_state and client.game_state.move_number > old_move: return

async def game_loop(client: NetworkClient):
    game_started = asyncio.Event()
    game_ended = asyncio.Event()
    game_result = None
    def on_start(payload): game_started.set()
    def on_over(winner, result):
        nonlocal game_result
        game_result = (winner, result)
        game_ended.set()
    client.on_game_started = on_start
    client.on_game_over = on_over
    if client.state != ConnectionState.PLAYING:
        try: await asyncio.wait_for(game_started.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            print("❌ Таймаут ожидания начала игры")
            return
    while client.state == ConnectionState.PLAYING:
        clear_screen()
        print_network_state(client)
        if client.is_my_turn():
            print("\n💡 Ваш ход! Введите координаты (D4), 'pass', 'undo', 'chat <текст>', 'resign':")
            try:
                move_input = input(" > ").strip()
                if not move_input: continue
                cmd = move_input.split(maxsplit=1)
                action = cmd[0].lower()
                if action == "help": show_help(); input("\nНажмите Enter...")
                elif action == "pass": await client.send_pass(); print("⏭️ Вы пасовали"); await asyncio.sleep(0.5)
                elif action == "undo": await client.request_undo(); print("⏳ Запрос отправлен..."); await asyncio.sleep(1)
                elif action == "resign" or action == "quit":
                    if input("❓ Точно сдаться/выйти? (yes/no): ").strip().lower() == "yes": await client.send_resign(); break
                elif action == "chat":
                    if len(cmd) > 1: await client.send_chat(cmd[1])
                else:
                    # Простой парсер координат (A1 -> x=0, y=0)
                    try:
                        col = action[0].upper()
                        row = int(action[1:])
                        x = ord(col) - ord('A')
                        if x >= 8: x -= 1  # Пропуск I
                        y = row - 1
                        success = await client.send_move(x, y)
                        if not success: print("❌ Ход не отправлен"); await asyncio.sleep(1)
                    except ValueError: print("❌ Неверные координаты"); await asyncio.sleep(1)
            except KeyboardInterrupt: break
        else:
            print("\n⏳ Ожидание хода противника...")
            try: await asyncio.wait_for(wait_for_state_update(client), timeout=60.0)
            except asyncio.TimeoutError: print("⚠️ Долгое ожидание..."); await asyncio.sleep(1)
    if game_result:
        clear_screen()
        print("\n" + "=" * 60)
        print("🏆 ИГРА ОКОНЧЕНА! ")
        print("=" * 60)
        winner, result_str = game_result
        my_color_str = client.player_color
        if winner == my_color_str: print("🎉 ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!")
        elif winner == "draw": print("🤝 НИЧЬЯ!")
        else: print("😔 Вы проиграли...")
        print(f"📊 Результат: {result_str}")
        print("=" * 60)
        input("\nНажмите Enter для возврата...")

async def run_network_game():
    parser = argparse.ArgumentParser(description="OS-GO Network PvP")
    parser.add_argument("--server", default="ws://localhost:8765")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()
    player_name = args.name or input("Введите ваше имя: ").strip() or "Player"
    client = NetworkClient(args.server, player_name)
    clear_screen()
    print("=" * 60)
    print("         ПОДКЛЮЧЕНИЕ К СЕРВЕРУ... ")
    print("=" * 60)
    print(f"🌐 Сервер: {args.server}")
    print(f"👤 Имя: {player_name}")
    if not await client.connect():
        print("❌ Не удалось подключиться к серверу")
        input("\nНажмите Enter...")
        return
    print("✅ Подключено!")
    await asyncio.sleep(0.5)
    try:
        while True:
            in_room = await lobby_menu(client)
            if not in_room: break
            game_ready = await room_wait_menu(client)
            if not game_ready: continue
            await game_loop(client)
            client.state = ConnectionState.CONNECTED
            client.room_id = None
            client.game_state = None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()
        print("👋 Отключено от сервера")

if __name__ == "__main__":
    try: asyncio.run(run_network_game())
    except KeyboardInterrupt: print("\n👋 До свидания!")