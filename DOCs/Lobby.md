


## Содержание
- [Содержание](#содержание)
- [Архитектура](#архитектура)
- [Что изменилось в бэкенде](#что-изменилось-в-бэкенде)
  - [1. `client_adapted.py`](#1-client_adaptedpy)
  - [2. `server_adapted.py`](#2-server_adaptedpy)
  - [3. `output_interface_adapted.py`](#3-output_interface_adaptedpy)
  - [4. `protocol_adapted.py`](#4-protocol_adaptedpy)
- [Qt-обёртка над NetworkClient](#qt-обёртка-над-networkclient)
  - [Важные нюансы обёртки](#важные-нюансы-обёртки)
- [Реализация GameOutputInterface для GUI](#реализация-gameoutputinterface-для-gui)
- [Жизненный цикл сетевой игры](#жизненный-цикл-сетевой-игры)
- [Asyncio + Qt Event Loop](#asyncio--qt-event-loop)
  - [Проблема](#проблема)
  - [Решение: Отдельный поток для asyncio](#решение-отдельный-поток-для-asyncio)
  - [Альтернатива: qasync](#альтернатива-qasync)
- [Обработка сигналов](#обработка-сигналов)
  - [Паттерн "State polling vs Push"](#паттерн-state-polling-vs-push)
  - [Thread-safety гарантии](#thread-safety-гарантии)
- [Чек-лист интеграции](#чек-лист-интеграции)
- [Файлы](#файлы)

---

## Архитектура

```
┌─────────────────────────────────────────────┐
│              PySide6 Frontend               │
│  ┌─────────────┐      ┌─────────────────┐   │
│  │  GoBoard    │◄────►│ NetworkClient   │   │
│  │  (QWidget)  │      │   (QObject)     │   │
│  └─────────────┘      └────────┬────────┘   │
│         ▲                        │           │
│         │                        │ WebSocket │
│  ┌──────┴──────┐                │           │
│  │ GameOutput   │                ▼           │
│  │ (QTextEdit,  │      ┌─────────────────┐   │
│  │  QTableView) │      │   GameServer    │   │
│  └──────────────┘      │   (asyncio)     │   │
└────────────────────────┴─────────────────┘
```

**Принцип:** `NetworkClient` остаётся чистым asyncio-классом. Для Qt создаётся тонкая `QObject`-обёртка, которая:
1. Переводит колбэки клиента в `pyqtSignal`
2. Запускает asyncio-цикл в отдельном потоке
3. Предоставляет thread-safe доступ к состоянию игры

---

## Что изменилось в бэкенде

### 1. `client_adapted.py`

| Проблема | Решение |
|----------|---------|
| Дублирование `get_sgf()` и `save_game()` | Удалено, оставлен один метод каждый |
| Колбэки не thread-safe | Добавлен `threading.RLock()` на всё состояние |
| `wait_for_state_change()` блокирует asyncio | Помечен как "не использовать в GUI", заменить на сигналы |
| Нет метода получения `go.Move` из истории | Добавлен `get_last_move_as_object()` для KataGo-анализа |
| `player_left` передавал `"unknown"` | Теперь передаёт реальное имя из payload |

**Ключевые методы для GUI:**
- `get_display_state()` — возвращает копию состояния (thread-safe)
- `get_move_history()` — копия истории для SGF/анализа
- `get_local_board()` — создаёт `go.Board` для KataGo
- `get_connection_state()` — текущий статус подключения

### 2. `server_adapted.py`

| Проблема | Решение |
|----------|---------|
| Дублирование кода `game_over` в `handle_game_move`/`handle_game_pass` | Вынесено в `_finalize_game()` |
| `calculate_score()` захардкожен под Windows `.exe` | Теперь ищет `gnugo` в `PATH` и относительно скрипта |
| `undo_request` не возвращал `opponent_id` | Исправлено, добавлен `get_opponent_id()` |
| Отключение игрока во время игры не обрабатывалось | `handle_player_disconnect()` завершает игру с победой оппонента |
| `broadcast` падал если один клиент отвалился | Ошибки изолируются по клиентам (`_send_safe`) |

### 3. `output_interface_adapted.py`

| Проблема | Решение |
|----------|---------|
| Дублирование `clear_screen` и `show_game_state` | Удалено |
| `get_input()` блокирующий | Добавлен `show_prompt(prompt, callback)` для GUI |
| Нет методов для чата и статуса | Добавлены `show_chat_message()`, `set_connection_status()` |

### 4. `protocol_adapted.py`

- Добавлен `GameAction.dict_to_move()` — десериализация хода из сетевого сообщения в `go.Move`
- Полезно для рендеринга истории ходов и вариаций в GUI

---

## Qt-обёртка над NetworkClient

Создайте файл `network_client_wrapper.py`:

```python
from PySide6.QtCore import QObject, Signal, QThread, QMetaObject, Qt
from PySide6.QtWidgets import QApplication
import asyncio
import sys

# Предполагается, что client_adapted.py и protocol_adapted.py доступны
from client_adapted import NetworkClient, ConnectionState
from protocol_adapted import RoomInfo


class AsyncioThread(QThread):
    """Поток с собственным asyncio event loop."""
    def __init__(self):
        super().__init__()
        self.loop = None
        self._running = True

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self._running = False
        self.wait(2000)

    def submit(self, coro):
        """Безопасный вызов корутины из GUI-потока."""
        if self.loop and self._running:
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)
            return future
        return None


class QtNetworkClient(QObject):
    """
    QObject-обёртка над NetworkClient.
    Все сигналы безопасно эмитятся из asyncio-колбэков.
    """

    # --- Сигналы для GUI ---
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str, str)          # code, message
    room_list_received = Signal(list)          # List[RoomInfo]
    room_joined = Signal(str, str)             # room_id, color
    room_updated = Signal(dict)                # payload
    game_started = Signal(dict)                # payload
    game_state_changed = Signal(object)        # GameDisplayState
    move_received = Signal(dict)               # move dict
    game_over = Signal(str, str, str)          # winner, result, sgf
    player_joined = Signal(list)               # players list
    player_left = Signal(str)                  # player_name
    chat_message = Signal(str, str)            # sender, text
    undo_requested = Signal(str)               # requester name
    undo_responded = Signal(bool)              # accepted

    def __init__(self, server_url: str, player_name: str, parent=None):
        super().__init__(parent)
        self._client = NetworkClient(server_url, player_name)
        self._thread = AsyncioThread()
        self._thread.start()

        # Подключаем колбэки клиента к сигналам через invokeMethod
        self._client.on_connected = self._emit_connected
        self._client.on_disconnected = self._emit_disconnected
        self._client.on_error = self._emit_error
        self._client.on_room_list = self._emit_room_list
        self._client.on_room_joined = self._emit_room_joined
        self._client.on_room_update = self._emit_room_updated
        self._client.on_game_started = self._emit_game_started
        self._client.on_game_state_update = self._emit_game_state
        self._client.on_move_received = self._emit_move
        self._client.on_game_over = self._emit_game_over
        self._client.on_player_joined = self._emit_player_joined
        self._client.on_player_left = self._emit_player_left
        self._client.on_chat_message = self._emit_chat
        self._client.on_undo_request = self._emit_undo_request
        self._client.on_undo_response = self._emit_undo_response

    # --- Колбэки-адаптеры (вызываются из asyncio-потока) ---
    def _emit_connected(self):
        QMetaObject.invokeMethod(self, "connected", Qt.QueuedConnection)
    def _emit_disconnected(self):
        QMetaObject.invokeMethod(self, "disconnected", Qt.QueuedConnection)
    def _emit_error(self, code, msg):
        QMetaObject.invokeMethod(self, "error_occurred", Qt.QueuedConnection,
                                 code, msg)
    def _emit_room_list(self, rooms):
        QMetaObject.invokeMethod(self, "room_list_received", Qt.QueuedConnection,
                                 rooms)
    def _emit_room_joined(self, rid, color):
        QMetaObject.invokeMethod(self, "room_joined", Qt.QueuedConnection,
                                 rid, color)
    def _emit_room_updated(self, payload):
        QMetaObject.invokeMethod(self, "room_updated", Qt.QueuedConnection,
                                 payload)
    def _emit_game_started(self, payload):
        QMetaObject.invokeMethod(self, "game_started", Qt.QueuedConnection,
                                 payload)
    def _emit_game_state(self, state):
        # state здесь — внутренний GameState, конвертируем в GameDisplayState
        display = self._client.get_display_state()
        if display:
            QMetaObject.invokeMethod(self, "game_state_changed", Qt.QueuedConnection,
                                     display)
    def _emit_move(self, move):
        QMetaObject.invokeMethod(self, "move_received", Qt.QueuedConnection,
                                 move)
    def _emit_game_over(self, winner, result, sgf=None):
        QMetaObject.invokeMethod(self, "game_over", Qt.QueuedConnection,
                                 winner, result, sgf or "")
    def _emit_player_joined(self, players):
        QMetaObject.invokeMethod(self, "player_joined", Qt.QueuedConnection,
                                 players)
    def _emit_player_left(self, name):
        QMetaObject.invokeMethod(self, "player_left", Qt.QueuedConnection,
                                 name)
    def _emit_chat(self, sender, text):
        QMetaObject.invokeMethod(self, "chat_message", Qt.QueuedConnection,
                                 sender, text)
    def _emit_undo_request(self, requester):
        QMetaObject.invokeMethod(self, "undo_requested", Qt.QueuedConnection,
                                 requester)
    def _emit_undo_response(self, accepted):
        QMetaObject.invokeMethod(self, "undo_responded", Qt.QueuedConnection,
                                 accepted)

    # --- Публичные методы (вызываются из GUI-потока) ---
    def connect_to_server(self):
        self._thread.submit(self._client.connect())

    def disconnect_from_server(self):
        self._thread.submit(self._client.disconnect())

    def create_room(self, name, size=19, password=None, komi=6.5, rules="japanese"):
        self._thread.submit(self._client.create_room(name, size, password, komi, rules))

    def join_room(self, room_id, password=None):
        self._thread.submit(self._client.join_room(room_id, password))

    def leave_room(self):
        self._thread.submit(self._client.leave_room())

    def set_ready(self, ready=True):
        self._thread.submit(self._client.set_ready(ready))

    def send_move(self, x, y):
        self._thread.submit(self._client.send_move(x, y))

    def send_pass(self):
        self._thread.submit(self._client.send_pass())

    def send_resign(self):
        self._thread.submit(self._client.send_resign())

    def request_undo(self):
        self._thread.submit(self._client.request_undo())

    def send_chat(self, text):
        self._thread.submit(self._client.send_chat(text))

    def get_display_state(self):
        """Thread-safe чтение состояния (можно вызывать из GUI)."""
        return self._client.get_display_state()

    def get_move_history(self):
        return self._client.get_move_history()

    def get_sgf(self):
        return self._client.get_sgf()

    def save_game(self, filepath=None):
        return self._client.save_game(filepath)

    def shutdown(self):
        self._thread.submit(self._client.disconnect())
        self._thread.stop()
```

### Важные нюансы обёртки

1. **QMetaObject.invokeMethod** с `Qt.QueuedConnection` гарантирует, что сигналы обработаются в GUI-потоке, даже если колбэк пришёл из asyncio-потока.
2. **AsyncioThread** изолирует event loop WebSocket от Qt event loop, избегая конфликтов.
3. Все `submit()` возвращают `concurrent.futures.Future`, но в GUI обычно достаточно "fire and forget".

---

## Реализация GameOutputInterface для GUI

```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QPushButton, QLineEdit, QTextEdit,
                                 QTableWidget, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, Signal
from output_interface_adapted import GameOutputInterface, GameDisplayState, RoomDisplayState, MessageData


class QtGameOutput(QWidget, GameOutputInterface):
    """
    Пример GUI-реализации интерфейса вывода.
    Можно разделить на несколько виджетов (доска, чат, лобби).
    """

    move_input = Signal(str)  # Для координат хода

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Статус
        self.status_label = QLabel("Отключено")
        layout.addWidget(self.status_label)
        
        # Доска (упрощённо — можно заменить на кастомный виджет)
        self.board_label = QLabel("Доска")
        layout.addWidget(self.board_label)
        
        # Чат
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Ввод чата
        chat_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Сообщение...")
        chat_layout.addWidget(self.chat_input)
        self.btn_send = QPushButton("Отправить")
        chat_layout.addWidget(self.btn_send)
        layout.addLayout(chat_layout)
        
        # Лобби (таблица комнат)
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(6)
        self.rooms_table.setHorizontalHeaderLabels(
            ["ID", "Название", "Хост", "Размер", "Игроки", "Статус"]
        )
        layout.addWidget(self.rooms_table)

    # --- GameOutputInterface ---

    def clear_screen(self):
        self.chat_display.clear()
        self.board_label.setText("")

    def show_game_state(self, state: GameDisplayState):
        text = f"Ход {state.move_number} | {state.current_player}"
        if state.is_my_turn:
            text += " (ВАШ ХОД!)"
        self.status_label.setText(text)
        # Здесь вызовите обновление кастомного виджета доски
        self._render_board(state.board_array, state.board_size, state.last_move)

    def _render_board(self, array, size, last_move):
        # Упрощённый текстовый рендер для примера
        lines = []
        for y in range(size):
            row = []
            for x in range(size):
                val = array[y][x] if y < len(array) and x < len(array[y]) else 0
                if last_move and last_move.get("x") == x and last_move.get("y") == y:
                    c = "[X]" if val == 1 else "[O]" if val == 2 else "[+]"
                else:
                    c = " X " if val == 1 else " O " if val == 2 else " . "
                row.append(c)
            lines.append("".join(row))
        self.board_label.setText("\\n".join(lines))

    def show_message(self, message: MessageData):
        if message.type == "error":
            QMessageBox.critical(self, "Ошибка", message.text)
        elif message.type == "success":
            QMessageBox.information(self, "Успех", message.text)
        else:
            self.chat_display.append(f"[{message.type.upper()}] {message.text}")

    def show_board(self, board_array, size, last_move=None):
        self._render_board(board_array, size, last_move)

    def show_game_result(self, winner: str, result: str, reason: str):
        QMessageBox.information(
            self, "Игра окончена",
            f"Победитель: {winner}\\nРезультат: {result}\\nПричина: {reason}"
        )

    def show_room_state(self, state: RoomDisplayState):
        self.status_label.setText(f"Комната {state.room_id} | Вы: {state.my_color}")

    def show_room_list(self, rooms: list):
        self.rooms_table.setRowCount(len(rooms))
        for i, room in enumerate(rooms):
            self.rooms_table.setItem(i, 0, QTableWidgetItem(str(room.get("room_id", ""))))
            self.rooms_table.setItem(i, 1, QTableWidgetItem(str(room.get("name", ""))))
            self.rooms_table.setItem(i, 2, QTableWidgetItem(str(room.get("host_name", ""))))
            bs = room.get("board_size", 19)
            self.rooms_table.setItem(i, 3, QTableWidgetItem(f"{bs}x{bs}"))
            pc = room.get("player_count", 0)
            mp = room.get("max_players", 2)
            self.rooms_table.setItem(i, 4, QTableWidgetItem(f"{pc}/{mp}"))
            self.rooms_table.setItem(i, 5, QTableWidgetItem(str(room.get("status", ""))))

    def get_input(self, prompt: str) -> str:
        # В GUI не используем блокирующий ввод
        return ""

    def show_help(self):
        QMessageBox.information(self, "Справка",
            "Координаты: A1-T19 (без I)\\n"
            "pass — пропустить ход\\n"
            "undo — отменить ход\\n"
            "resign — сдаться")

    # --- GUI-специфичные ---

    def show_chat_message(self, sender: str, text: str):
        self.chat_display.append(f"&lt;{sender}&gt; {text}")

    def set_connection_status(self, status: str, details: str = ""):
        self.status_label.setText(f"{status} {details}")
```

---

## Жизненный цикл сетевой игры

```
[GUI] Нажата кнопка "Подключиться"
  → QtNetworkClient.connect_to_server()
    → AsyncioThread: client.connect()
      → WebSocket handshake
      ← Signal: connected()

[GUI] Получен сигнал connected()
  → Показать лобби
  → Автоматически придёт room_list_received

[GUI] Нажата "Создать комнату"
  → QtNetworkClient.create_room(name, size, ...)
  ← Signal: room_joined(room_id, color)
  → Показать экран ожидания

[GUI] Нажата "Готов"
  → QtNetworkClient.set_ready(True)
  ← Signal: room_updated (оба игрока готовы)
  ← Signal: game_started(payload)
  → Показать доску

[GUI] Клик по доске (x, y)
  → QtNetworkClient.send_move(x, y)
  ← Signal: move_received(move)  [подтверждение сервера]
  ← Signal: game_state_changed(state)
  → Перерисовать доску

[GUI] Противник сделал ход
  ← Signal: move_received(move)
  ← Signal: game_state_changed(state)
  → Перерисовать доску, показать "ВАШ ХОД"

[GUI] Два паса / сдача / отключение
  ← Signal: game_over(winner, result, sgf)
  → Показать результат, предложить сохранить SGF
```

---

## Asyncio + Qt Event Loop

### Проблема
PySide6 использует свой `QEventLoop`. `asyncio` использует свой `EventLoop`. Они несовместимы.

### Решение: Отдельный поток для asyncio
(Реализовано в `AsyncioThread` выше)

```python
class AsyncioThread(QThread):
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
```

### Альтернатива: qasync
Если хотите использовать один цикл, можно применить библиотеку `qasync`:

```python
import qasync
from qasync import QEventLoop

app = QApplication(sys.argv)
loop = QEventLoop(app)
asyncio.set_event_loop(loop)

# Теперь можно использовать asyncio.run() вместе с Qt
with loop:
    loop.run_forever()
```

**Но:** `websockets` может конфликтовать с `QEventLoop` при высокой нагрузке. Рекомендуется **отдельный поток** для стабильности.

---

## Обработка сигналов

### Паттерн "State polling vs Push"

**Push (рекомендуется):**
GUI обновляется только по сигналам. Не нужен таймер.

```python
self.client.game_state_changed.connect(self.board_widget.update_state)
self.client.move_received.connect(self.board_widget.animate_last_move)
```

**Polling (если нужно):**
Если требуется принудительное обновление (например, таймер хода):

```python
from PySide6.QtCore import QTimer

timer = QTimer(self)
timer.timeout.connect(self._refresh_state)
timer.start(1000)  # 1 сек

def _refresh_state(self):
    state = self.client.get_display_state()
    if state:
        self.update_board(state)
```

### Thread-safety гарантии

Все `get_*` методы `NetworkClient` используют `RLock`. Можно вызывать из GUI-потока безопасно.

Но **не модифицируйте** внутреннее состояние `NetworkClient` напрямую из GUI — только через `submit()`.

---

## Чек-лист интеграции

- [ ] Скопировать `client_adapted.py`, `server_adapted.py`, `protocol_adapted.py`, `output_interface_adapted.py` в проект
- [ ] Создать `QtNetworkClient` (QObject-обёртка) с `AsyncioThread`
- [ ] Реализовать `GameOutputInterface` через Qt-виджеты
- [ ] Подключить сигналы `game_state_changed` к виджету доски
- [ ] Обработать `game_over` — показать диалог с результатом и кнопкой "Сохранить SGF"
- [ ] Добавить KataGo-анализ через `client.get_local_board()` + `KataGoAnalyzer`
- [ ] Обработать `undo_requested` — показать диалог "Принять отмену хода?"
- [ ] Обработать `player_left` / `disconnected` — вернуть в лобби
- [ ] Протестировать: создание комнаты, вход, готовность, ход, пас, сдача, отключение

---

## Файлы

| Файл | Назначение |
|------|------------|
| `client_adapted.py` | Клиентская библиотека (thread-safe, без дублей) |
| `server_adapted.py` | Сервер (унифицированное завершение игры, кроссплатформенный scoring) |
| `protocol_adapted.py` | Протокол (dict→Move для GUI) |
| `output_interface_adapted.py` | Интерфейс вывода (GUI-friendly методы) |
| `PySide6_Integration.md` | Эта документация |
'''

with open('/mnt/agents/output/PySide6_Integration.md', 'w', encoding='utf-8') as f:
    f.write(doc)

print("PySide6_Integration.md written")
