"""
unified_game_loop.py
====================
Единый игровой цикл для локальной и сетевой игры.
"""

import asyncio
import sys
from output_interface import get_output_interface, OutputType, MessageData
from game_controller import GameController

_output = get_output_interface(OutputType.CONSOLE)


async def ainput(prompt: str = "") -> str:
    """Асинхронный ввод (не блокирует WebSocket)"""
    loop = asyncio.get_event_loop()
    # Явный flush, чтобы prompt гарантированно появился до блокировки
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    return await loop.run_in_executor(None, sys.stdin.readline)


async def run_unified_loop(controller: GameController):
    input_task: Optional[asyncio.Task] = None

    while not controller.is_game_over():
        _output.clear_screen()
        disp = controller.get_display_state()
        if disp:
            _output.show_game_state(disp)

        if controller.is_game_over():
            break

        if controller.is_my_turn():
            if input_task is None:
                input_task = asyncio.create_task(ainput(""))

            # Параллельно ждём: ввод, обновление состояния или конец игры
            update_task = asyncio.create_task(controller.wait_for_update())
            over_task = asyncio.create_task(controller.wait_for_game_over())

            done, pending = await asyncio.wait(
                [input_task, update_task, over_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Отменяем только вспомогательные задачи; input_task оставляем жить
            for task in pending:
                if task is not input_task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            if controller.is_game_over():
                if input_task and not input_task.done():
                    input_task.cancel()
                break

            # Если сработало обновление состояния (chat, и т.д.) — просто перерисуем
            if input_task not in done:
                continue

            # Ввод получен
            try:
                cmd = input_task.result().strip()
            except asyncio.CancelledError:
                continue
            finally:
                input_task = None

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

    # Проглатываем возможный висящий ввод из комнаты/цикла
    if input_task and not input_task.done():
        input_task.cancel()
    await asyncio.sleep(0.1)

    await ainput("\nНажмите Enter для возврата...")