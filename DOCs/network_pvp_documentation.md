# OS-GO Network PvP — Документация

## Содержание
1. [Обзор архитектуры](#1-обзор-архитектуры)
2. [Сетевой протокол](#2-сетевой-протокол)
3. [Сервер](#3-сервер)
4. [Клиент](#4-клиент)
5. [PySide6 GUI](#5-pyside6-gui)
6. [Интеграция с движком](#6-интеграция-с-движком)
7. [Поток данных](#7-поток-данных)
8. [Жизненный цикл игры](#8-жизненный-цикл-игры)
9. [Расширение и кастомизация](#9-расширение-и-кастомизация)

---

## 1. Обзор архитектуры

Подсистема онлайн-игры (`network_pvp/`) реализует полноценный клиент-серверный мультиплеер для игры в Го с поддержкой:
- **WebSocket** соединений (библиотека `websockets`)
- **Лобби** с комнатами, паролями и статусом готовности
- **Синхронизации игрового состояния** через `go_engine`
- **PySide6 GUI** с асинхронной интеграцией
- **Консольного режима** через единый игровой цикл
- **Отмены ходов, чата, сохранения SGF**

### Структура модулей

```
network_pvp/
├── protocol.py          # Сериализация сообщений, типы, хелперы
├── server.py            # WebSocket-сервер, лобби, игровые комнаты
├── client.py            # Асинхронный клиент, thread-safe состояние
├── pyside_npvp.py       # PySide6 GUI (окна, доска, чат)
├── output_interface.py  # Абстракция вывода (console/UI/network)
└── __init__.py
```

### Взаимодействие с корневой директорией

```
config.py              # Пути для сохранения SGF, поддиректории игр
core_adapter.py        # GameSession — обёртка над go_engine
                       # CoordinateUtils, PlayerType, MoveResult
game_controller.py     # GameController (ABC) — единый интерфейс
                       # LocalController / NetworkController
unified_game_loop.py   # Единый асинхронный игровой цикл
console_back.py        # Консольный рендеринг (справка, тесты)
```

---

## 2. Сетевой протокол

**Файл:** `protocol.py`

### 2.1 Формат сообщений

Все сообщения сериализуются в JSON:

```json
{
  "type": "game_move",
  "payload": {
    "x": 3,
    "y": 4,
    "move_number": 15
  }
}
```

### 2.2 Типы сообщений (`MessageType`)

| Тип | Направление | Описание |
|-----|-------------|----------|
| `CONNECT` | C→S | Подключение игрока (имя, версия) |
| `DISCONNECT` | C→S | Отключение |
| `ERROR` | S→C | Ошибка протокола |
| `ROOM_LIST` | S→C | Список доступных комнат |
| `ROOM_CREATE` | C→S | Создание комнаты (имя, размер, пароль, коми, правила) |
| `ROOM_JOIN` | C→S / S→C | Вход в комнату |
| `ROOM_LEAVE` | C→S | Выход из комнаты |
| `ROOM_UPDATE` | S→C | Обновление состава/готовности |
| `ROOM_READY` | C→S | Статус готовности |
| `GAME_START` | S→C | Начало игры (начальное состояние) |
| `GAME_MOVE` | C→S / S→C | Ход на доску |
| `GAME_PASS` | C→S / S→C | Пас |
| `GAME_RESIGN` | C→S | Сдача |
| `GAME_UNDO_REQUEST` | C→S / S→C | Запрос отмены хода |
| `GAME_UNDO_RESPONSE` | C→S / S→C | Ответ на запрос отмены |
| `GAME_STATE` | S→C | Полное состояние доски |
| `GAME_OVER` | S→C | Игра окончена (победитель, SGF) |
| `GAME_CHAT` | C→S / S→C | Сообщение в чат |
| `LOBBY_READY` | C→S | Запрос списка комнат |

### 2.3 Ключевые структуры данных

```python
@dataclass
class RoomInfo:
    room_id: str          # UUID (первые 8 символов)
    name: str
    host_name: str
    board_size: int       # 9, 13, 19
    has_password: bool
    player_count: int     # 0-2
    max_players: int      # = 2
    status: str           # "waiting" | "playing" | "finished"

@dataclass
class PlayerInfo:
    player_id: str
    name: str
    color: Optional[str]  # "black" | "white" | None
    is_ready: bool
    is_connected: bool

class PlayerColor(Enum):
    BLACK = "black"
    WHITE = "white"
    SPECTATOR = "spectator"
```

### 2.4 Хелперы конвертации (`GameAction`)

Статические методы для преобразования между `go_engine` и сетевыми структурами:

```python
GameAction.color_to_str(go.Color.Black)   # -> "black"
GameAction.str_to_color("white")          # -> go.Color.White
GameAction.board_to_array(board)          # -> List[List[int]]
GameAction.move_to_dict(move)             # -> dict для JSON
GameAction.dict_to_move(data)             # -> go.Move (для GUI-рендеринга)
```

### 2.5 Фабричные методы `Message`

```python
Message.connect(player_name="Alice", version="1.0")
Message.room_create(name="Dojo", board_size=19, password="123", komi=6.5, rules="japanese")
Message.game_move(x=3, y=4, move_number=15)
Message.game_state(board_array=..., current_player="black", move_number=15, passes=0)
Message.game_over(winner="black", result="B+3.5", reason="two_passes", sgf="(...)")
```

---

## 3. Сервер

**Файл:** `server.py`

### 3.1 Архитектура сервера

```
GameServer
├── host: str, port: int
├── lobby: Lobby              # Управление комнатами
├── connections: Dict[ws, conn_info]  # Все WebSocket-подключения
└── players: Dict[player_id, player_info]
```

### 3.2 Компоненты

#### `GameRoom` — Игровая комната

Жизненный цикл: `waiting` → `playing` → `finished`

**Свойства:**
- `players: Dict[str, RoomPlayer]` — до 2 игроков
- `spectators: Dict[str, RoomPlayer]` — зрители (резерв)
- `session: GameSession` — экземпляр игрового движка
- `move_history: List[dict]` — история ходов для SGF
- `pending_undo: Optional[str]` — ID игрока, запросившего отмену

**Методы:**
```python
room.add_player(player)           # Автоматическое назначение цвета
room.remove_player(player_id)     # Передача хоста при выходе
room.set_ready(player_id, True)   # Готовность к игре
room.start_game()                 # Запуск при all_ready()
room.make_move(player_id, x, y)   # Валидация + выполнение
room.make_pass(player_id)         # Пас
room.request_undo(player_id)      # Запрос отмены (требует подтверждения)
room.confirm_undo(accepted)       # Подтверждение/отклонение
room.resign(player_id)            # Сдача
room.calculate_score()            # Подсчёт через GNU Go Analyzer
room.handle_player_disconnect()   # Автопобеда оппонента при дисконнекте
room.broadcast(message, exclude)  # Рассылка всем игрокам
```

#### `Lobby` — Менеджер комнат

```python
lobby.create_room(name, host_id, host_ws, host_name, **kwargs) -> GameRoom
lobby.join_room(room_id, player_id, player_ws, player_name, password) -> GameRoom
lobby.leave_room(player_id) -> Optional[GameRoom]
lobby.get_room_list() -> List[RoomInfo]
lobby.get_player_room(player_id) -> Optional[GameRoom]
```

### 3.3 Обработчики сообщений сервера

| Метод | Логика |
|-------|--------|
| `handle_connect` | Регистрация имени, аутентификация |
| `handle_lobby_ready` | Отправка списка комнат |
| `handle_room_create` | Создание комнаты, авто-вход хоста |
| `handle_room_join` | Валидация пароля, проверка заполненности, рассылка обновления |
| `handle_room_ready` | Установка готовности, авто-старт при 2×ready |
| `handle_game_move` | Валидация хода, broadcast GAME_STATE, проверка game_over |
| `handle_game_pass` | Пас, broadcast, проверка двойного паса |
| `handle_game_resign` | Сдача → `_finalize_game` |
| `handle_game_undo_request` | Отправка запроса оппоненту |
| `handle_game_undo_response` | Применение/отклонение отмены |
| `handle_game_chat` | Сохранение в историю, broadcast |
| `disconnect` | Обработка дисконнекта: game_over при активной игре |

### 3.4 Завершение игры (`_finalize_game`)

1. Установка статуса `finished`
2. Подсчёт очков через `calculate_score()` (GNU Go Analyzer)
3. Формирование SGF из `session.game.get_sgf()`
4. Определение победителя
5. Broadcast `GAME_OVER` с SGF-записью

### 3.5 Запуск сервера

```bash
python server.py --host 0.0.0.0 --port 8765
```

---

## 4. Клиент

**Файл:** `client.py`

### 4.1 Архитектура клиента

```
NetworkClient
├── server_url: str
├── player_name: str
├── ws: WebSocketClientProtocol
├── state: ConnectionState
├── player_id / player_color / room_id
├── _game_state: GameState (thread-safe через RLock)
├── _move_history: List[dict]
└── on_* callbacks: Callable (для интеграции с GUI)
```

### 4.2 Состояния подключения (`ConnectionState`)

```python
DISCONNECTED → CONNECTING → CONNECTED → IN_ROOM → PLAYING
                                    ↖___________↙ (после GAME_OVER)
```

### 4.3 Thread-safe доступ

Все операции чтения состояния защищены `threading.RLock()`:

```python
client.get_display_state()      # -> GameDisplayState
client.get_move_history()       # -> List[dict]
client.get_connection_state()   # -> ConnectionState
client.is_my_turn()             # -> bool
client.get_sgf()                # -> str (формирует из истории)
client.save_game(filepath)      # -> Optional[str] (путь к файлу)
client.get_local_board()        # -> go.Board (для KataGo-анализа)
```

### 4.4 Сетевые методы (async)

```python
await client.connect()                    # WebSocket + CONNECT + LOBBY_READY
await client.disconnect()                 # Graceful shutdown
await client.create_room(name, size, ...) # ROOM_CREATE
await client.join_room(room_id, password) # ROOM_JOIN
await client.leave_room()                 # ROOM_LEAVE
await client.set_ready(is_ready)          # ROOM_READY
await client.send_move(x, y)              # GAME_MOVE (с проверкой очереди)
await client.send_pass()                  # GAME_PASS
await client.send_resign()                # GAME_RESIGN
await client.request_undo()               # GAME_UNDO_REQUEST
await client.send_chat(text)              # GAME_CHAT
```

### 4.5 Колбэки (для GUI-интеграции)

```python
client.on_connected = lambda: ...
client.on_room_list = lambda rooms: ...           # List[RoomInfo]
client.on_room_joined = lambda room_id, color: ...
client.on_game_started = lambda payload: ...
client.on_game_state_update = lambda state: ...   # GameState
client.on_move_received = lambda move: ...        # dict
client.on_game_over = lambda winner, result, sgf: ...
client.on_error = lambda code, message: ...
client.on_chat_message = lambda sender, text: ...
client.on_undo_request = lambda requester: ...
client.on_undo_response = lambda accepted: ...
```

**Важно:** Колбэки вызываются из asyncio-цикла. Для PySide6 используйте `QtNetworkClient` (см. раздел 5).

---

## 5. PySide6 GUI

**Файл:** `pyside_npvp.py`

### 5.1 Архитектура GUI

```
MainWindow (QMainWindow)
├── QStackedWidget (4 страницы)
│   ├── ConnectPage      # Ввод имени и адреса сервера
│   ├── LobbyPage        # Таблица комнат, создание/вход
│   ├── RoomPage         # Состав игроков, чат, готовность
│   └── GamePage         # Доска, чат, кнопки управления
└── QtNetworkClient      # QObject-обёртка над NetworkClient
```

### 5.2 `QtNetworkClient` — QObject-обёртка

Решает проблему интеграции asyncio и Qt:

```python
class QtNetworkClient(QObject):
    # Сигналы (thread-safe emit)
    connected = Signal()
    disconnected = Signal()
    error_occurred = Signal(str, str)       # code, message
    room_list_received = Signal(list)       # List[RoomInfo]
    room_joined = Signal(str, str)          # room_id, color
    game_state_changed = Signal(object)     # GameDisplayState
    move_received = Signal(dict)
    game_over = Signal(str, str, str)       # winner, result, sgf
    chat_message = Signal(str, str)         # sender, text
    undo_requested = Signal(str)            # requester name
    undo_responded = Signal(bool)           # accepted
```

**AsyncioThread:** Отдельный `QThread` с собственным `asyncio` event loop. Все корутины клиента выполняются в этом потоке, сигналы эмитируются в главный поток Qt.

### 5.3 Виджет доски (`GoBoardWidget`)

```python
class GoBoardWidget(QFrame):
    stone_clicked = Signal(int, int)  # x, y

    # Рендеринг:
    # - Фон: деревянная текстура (#dcb35c)
    # - Линии сетки
    # - Хоси-точки (звёзды) для 9×9, 13×13, 19×19
    # - Камни: ● черные, ○ белые
    # - Последний ход: красное кольцо
```

**Обработка клика:** `mousePressEvent` → `_to_board_coords()` → `stone_clicked.emit(x, y)`

### 5.4 Поток экранов

```
[Connect] --(подключение)--> [Lobby]
[Lobby] --(создание/вход)--> [Room]
[Room] --(все готовы)--> [Game]
[Game] --(игра окончена)--> [Lobby]
```

### 5.5 Диалоги

- **Создание комнаты:** `QDialog` с полями (название, размер 9/13/19, пароль, коми, правила)
- **Вход в комнату:** `QInputDialog` для пароля (если установлен)
- **Отмена хода:** `QMessageBox.question` с именем запросившего
- **Сохранение SGF:** `QFileDialog.getSaveFileName`

---

## 6. Интеграция с движком

### 6.1 `core_adapter.py` — GameSession

`GameSession` — центральная обёртка над `go_engine`:

```python
class GameSession:
    def __init__(self, board_size=19, komi=6.5, rules=go.Rules.Chinese):
        self.game = go.Game(board_size)    # go_engine.Game
        self.players: Dict[go.Color, Dict]  # name, type, gtp_color
        self.gnugo_bot: Optional[GNUGoBot]  # для PvE
```

**Ключевые методы для сетевой игры:**

```python
session.make_move(x, y, is_pass=False, by_color=None) -> MoveResult
# by_color: проверка очередности (для сетевых игр)

session.make_pass(by_color=None) -> MoveResult
session.resign(by_color) -> MoveResult
session.undo_move() -> bool
session.get_state_dict() -> Dict   # для отправки клиентам
session.save_game(game_mode) -> Optional[str]
```

### 6.2 `game_controller.py` — Единый интерфейс

```python
class GameController(ABC):
    def get_display_state(self) -> Optional[GameDisplayState]
    def is_game_over(self) -> bool
    def is_my_turn(self) -> bool
    async def execute_command(self, cmd: str) -> Dict
    async def wait_for_turn(self) -> None
```

**Реализации:**
- `LocalController` — обёртка над `GameSession` (PvP/PvE)
- `NetworkController` — обёртка над `NetworkClient`

`NetworkController.execute_command()` парсит команды:
- `"pass"` → `client.send_pass()`
- `"undo"` → `client.request_undo()`
- `"resign"` / `"quit"` → `client.send_resign()`
- `"chat <text>"` → `client.send_chat()`
- `"D4"` → `client.send_move(3, 3)`

### 6.3 `output_interface.py` — Абстракция вывода

```python
class GameOutputInterface(ABC):
    def show_game_state(self, state: GameDisplayState)
    def show_board(self, board_array, size, last_move)
    def show_game_result(self, winner, result, reason)
    def show_room_state(self, state: RoomDisplayState)
    def show_room_list(self, rooms)
    def get_input(self, prompt) -> str
```

`ConsoleOutput` — консольная реализация с цветными символами (○ ● · +).

### 6.4 `unified_game_loop.py`

Единый асинхронный цикл для всех режимов:

```python
async def run_unified_loop(controller: GameController):
    while not controller.is_game_over():
        # 1. Отрисовка состояния
        # 2. Если наш ход → ожидание ввода
        # 3. Если не наш ход → ожидание обновления
        # 4. Выполнение команды
    # Отображение результата
```

**Особенности сетевого режима:**
- `controller.wait_for_turn()` — блокируется до получения `GAME_STATE`
- `controller.wait_for_update()` — обработка чата, отмены и т.д.
- `ainput()` — асинхронный ввод (не блокирует WebSocket)

---

## 7. Поток данных

### 7.1 Создание комнаты и начало игры

```
[Client A]                    [Server]                    [Client B]
   |                             |                             |
   |-- CONNECT("Alice") -------->|                             |
   |                             |                             |
   |-- ROOM_CREATE("Dojo") ---->|                             |
   |<-- ROOM_JOIN(success) -----|                             |
   |                             |                             |
   |                             |<-- CONNECT("Bob") ----------|
   |                             |                             |
   |                             |<-- ROOM_JOIN("Dojo") -------|
   |<-- ROOM_UPDATE(Bob joined)-|-- ROOM_UPDATE(Bob joined) ->|
   |                             |                             |
   |-- ROOM_READY(true) ------->|                             |
   |                             |<-- ROOM_READY(true) --------|
   |                             |                             |
   |                             | [all_ready() -> start_game()]
   |                             |                             |
   |<-- GAME_START -------------|-- GAME_START -------------->|
   |  {board, current, players}  |  {board, current, players}  |
```

### 7.2 Ход в игре

```
[Client A (Black)]            [Server]                    [Client B (White)]
   |                             |                             |
   |-- GAME_MOVE(3,4) --------->|                             |
   |                             | [make_move() -> validate]   |
   |                             |                             |
   |<-- GAME_STATE -------------|-- GAME_STATE -------------->|
   |  {board, current: white}    |  {board, current: white}    |
   |                             |                             |
   |                             |<-- GAME_MOVE(5,6) ----------|
   |                             |                             |
   |<-- GAME_STATE -------------|-- GAME_STATE -------------->|
   |  {board, current: black}    |  {board, current: black}    |
```

### 7.3 Отмена хода

```
[Client A]                    [Server]                    [Client B]
   |                             |                             |
   |-- GAME_UNDO_REQUEST ------>|[request_undo()]             |
   |                             | [undo_move() -> success]    |
   |                             |                             |
   |                             |-- GAME_UNDO_REQUEST ------->|
   |                             |  {requester: "Alice"}       |
   |                             |                             |
   |                             |<-- GAME_UNDO_RESPONSE ------|
   |                             |  {accepted: true}           |
   |                             |                             |
   |<-- GAME_STATE --------------|-- GAME_STATE -------------->|
   |  {board after undo}         |  {board after undo}         |
```

### 7.4 Завершение игры (два паса)

```
[Client A]                    [Server]                    [Client B]
   |                             |                             |
   |-- GAME_PASS -------------->|[make_pass() -> two_passes]  |
   |                             |                             |
   |                             | [_finalize_game()]          |
   |                             | [calculate_score() via GNU] |
   |                             |                             |
   |<-- GAME_OVER ---------------|-- GAME_OVER -------------->|
   |  {winner, result, sgf}      |  {winner, result, sgf}      |
```

---

## 8. Жизненный цикл игры

### 8.1 Серверная сторона

```
waiting
  ├── player_joined → waiting (до 2 игроков)
  ├── player_ready → checking all_ready()
  │   └── all_ready() == True → playing
  │       ├── game_move / game_pass → playing (validate → broadcast)
  │       ├── game_resign → finished
  │       ├── disconnect during game → finished (opponent wins)
  │       └── two_passes → finished (_finalize_game)
  └── player_leave → waiting / destroyed (if empty)
```

### 8.2 Клиентская сторона

```
DISCONNECTED
  └── connect() → CONNECTED
        ├── create_room() / join_room() → IN_ROOM
        │     └── set_ready(True) → [ждём GAME_START]
        │           └── GAME_START → PLAYING
        │                 ├── send_move() / send_pass() → PLAYING
        │                 ├── request_undo() → PLAYING (pending)
        │                 ├── send_resign() → IN_ROOM [GAME_OVER]
        │                 └── GAME_OVER → IN_ROOM
        └── disconnect() → DISCONNECTED
```

---

## 9. Расширение и кастомизация

### 9.1 Добавление нового типа сообщения

1. **protocol.py:** Добавить в `MessageType`, создать фабричный метод
2. **server.py:** Реализовать `handle_<type>()` в `GameServer`
3. **client.py:** Реализовать `_on_<type>()` и колбэк
4. **pyside_npvp.py:** При необходимости — подключить сигнал

### 9.2 Кастомный GUI

```python
class MyGoUI(QObject):
    def __init__(self):
        self.client = QtNetworkClient("ws://localhost:8765", "Player")
        self.client.game_state_changed.connect(self.on_state)
        self.client.stone_clicked.connect(self.on_click)

    def on_state(self, state: GameDisplayState):
        # Рендеринг кастомной доски
        pass

    def on_click(self, x, y):
        self.client.send_move(x, y)
```

### 9.3 Консольный клиент

```python
from game_controller import NetworkController
from client import NetworkClient
from unified_game_loop import run_unified_loop

async def main():
    client = NetworkClient("ws://localhost:8765", "ConsolePlayer")
    await client.connect()
    await client.join_room("room_id")

    controller = NetworkController(client)
    await run_unified_loop(controller)

asyncio.run(main())
```

### 9.4 Подсчёт очков

Сервер использует `GnuGo_Analyzer` для подсчёта территории:
- Ищет `gnugo` в PATH и стандартных локациях
- Кроссплатформенный поиск (Windows/Linux)
- При недоступности GNU Go — fallback на простое определение победителя

---

## Приложение A: Зависимости

```
# Сервер
websockets >= 10.0

# Клиент (консоль)
websockets >= 10.0

# Клиент (GUI)
PySide6 >= 6.0
websockets >= 10.0

# Общее
go_engine (C++ биндинги)
GnuGo_Analyzer (опционально, для подсчёта)
```

## Приложение B: Запуск

```bash
# 1. Сервер
python network_pvp/server.py --host 0.0.0.0 --port 8765

# 2. GUI-клиент
python network_pvp/pyside_npvp.py

# 3. Консольный клиент (через unified_game_loop)
python PLAY_console.py  # если реализовано
```

## Приложение C: Формат SGF

Сервер и клиент поддерживают экспорт в SGF:
- GM[1] — игра Го
- FF[4] — формат 4
- SZ[N] — размер доски
- KM[N.N] — коми
- AP[OS-GO:Network:1.0] — приложение
- ;B[aa] / ;W[bb] — ходы
