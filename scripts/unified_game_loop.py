"""
unified_game_loop.py
====================
Единый игровой цикл для локальной и сетевой игры.
"""

import asyncio
from output_interface import get_output_interface, OutputType, MessageData
from game_controller import GameController

_output = get_output_interface(OutputType.CONSOLE)


async def ainput(prompt: str = "") -> str:
    """Асинхронный ввод (не блокирует WebSocket)"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: input(prompt).strip())


async def run_unified_loop(controller: GameController):
    """
    Универсальный цикл:
      - рисует доску через output_interface
      - принимает команды (ход, пас, undo, chat, resign)
      - для сетевой игры ждёт хода противника
    """
    while not controller.is_game_over():
        _output.clear_screen()

        disp = controller.get_display_state()
        if disp:
            _output.show_game_state(disp)

        if controller.is_game_over():
            break

        if controller.is_my_turn():
            cmd = await ainput(" > ")

            if not cmd:
                continue

            result = await controller.execute_command(cmd)

            if result.get('quit'):
                break

            if result.get('undo'):
                _output.show_message(MessageData(
                    "info" if result['success'] else "error",
                    result.get('message', 'Отмена хода')
                ))
                await asyncio.sleep(1)
                continue

            if not result['success']:
                _output.show_message(MessageData("error", result.get('message', 'Ошибка')))
                await asyncio.sleep(1)

        else:
            # Сетевая игра: ждём хода противника
            _output.show_message(MessageData("info", "Ожидание хода противника..."))
            await controller.wait_for_turn()

    # --- Итог игры ---
    result = controller.get_game_result()
    _output.clear_screen()

    if result:
        winner, result_str = result
        my_color = None
        if controller.get_mode() == "network":
            from game_controller import NetworkController
            if isinstance(controller, NetworkController):
                my_color = controller.client.player_color

        print("\n" + "=" * 60)
        print("🏆 ИГРА ОКОНЧЕНА!")
        print("=" * 60)
        print(f"📊 Результат: {result_str}")

        if controller.get_mode() == "network" and my_color:
            if winner == my_color:
                _output.show_message(MessageData("success", "ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!"))
            elif winner == "draw":
                _output.show_message(MessageData("info", "НИЧЬЯ!"))
            else:
                _output.show_message(MessageData("error", "Вы проиграли..."))
        else:
            print(f"🥇 Победитель: {winner}")

    await ainput("\nНажмите Enter для возврата...")