# OS-GO Network PvP — Документация интеграции

## Обзор архитектуры

┌─────────────┐      WebSocket      ┌─────────────┐
│  PySide6    │ ◄─────────────────► │   Server    │
│  Frontend   │    JSON Protocol    │  (Python)   │
│             │                     │  go_engine  │
└─────────────┘                     └─────────────┘
         │
         ▼
┌─────────────┐
│NetworkClient│  ← Переиспользуйте этот класс
│ (client.py) │
└─────────────┘
         │
         ▼
┌───────────────────┐
│ output_interface  │ ← Независимый вывод
│ (console/UI/...)  │
└───────────────────┘


## Изменения в версии 2.0

### 1. Исправление проблемы с лобби

**Проблема:** Лобби не обрабатывало команды с первого раза из-за гонки условий между подключением и отправкой списка комнат.

**Решение:** Добавлен двухэтапный протокол подключения:
1. Клиент отправляет `connect` для регистрации
2. Клиент отправляет `lobby_ready` для подтверждения готовности получить список комнат
3. Сервер отправляет список комнат только после получения `lobby_ready`

**Файлы:**
- `protocol.py`: Добавлен тип сообщения `LOBBY_READY`
- `server.py`: Добавлен обработчик `handle_lobby_ready`
- `client.py`: Обновлен метод `connect()` для отправки двух сообщений
- `console_network.py`: Убран дублирующий вызов connect из lobby_menu

### 2. Интеграция с локальным PvP/PvE кодом

**Цель:** Использовать готовые методы и функции из `console_back.py` и `core_adapter.py`

**Реализация:**
- Создан `output_interface.py` — независимый интерфейс вывода
- Интерфейс предоставляет те же функции, что и `console_back.py`:
  - `clear_screen()` — очистка экрана
  - `show_game_state()` — отображение состояния игры
  - `show_board()` — отображение доски
  - `show_message()` — показ сообщений
  - `show_game_result()` — результат игры
  - `get_input()` — ввод пользователя
  - `show_help()` — справка

**Преимущества:**
- Один код для консоли и будущего UI
- Легко добавлять новые интерфейсы 
- Совместимость с существующими функциями из `console_back.py`

### 3. Независимый вывод для UI

**output_interface.py** предоставляет:

#### Базовый класс `GameOutputInterface`:
```python
class GameOutputInterface(ABC):
    def clear_screen(self): ...
    def show_game_state(self, state: GameDisplayState): ...
    def show_message(self, message: MessageData): ...
    def show_board(self, board_array, size, last_move): ...
    def show_game_result(self, winner, result, reason): ...
    def show_room_state(self, state: RoomDisplayState): ...
    def show_room_list(self, rooms): ...
    def get_input(self, prompt) -> str: ...
    def show_help(self): ...
```

#### Классы данных:
- `GameDisplayState` — состояние игры для отображения
- `RoomDisplayState` — состояние комнаты
- `MessageData` — сообщение (тип + текст)

#### Готовые функции для импорта:
```python
from output_interface import (
    clear_screen,
    show_game_state,
    show_message,
    show_board,
    show_game_result,
    get_input,
    show_help
)
```

## Использование

### Запуск сервера:
```bash
cd scripts/network_pvp
python server.py --host 0.0.0.0 --port 8765
```

### Запуск клиента (консоль):
```bash
python console_network.py --server ws://localhost:8765 --name Player1
```

### Интеграция с UI:
```python
from output_interface import GameOutputInterface, GameDisplayState

class MyUIOutput(GameOutputInterface):
    def clear_screen(self):
        # Ваш код очистки UI
        pass

    def show_game_state(self, state: GameDisplayState):
        # Обновление UI элементами
        self.ui.board.update(state.board_array)
        self.ui.status.setText(f"Ход: {state.current_player}")
        # ...

# Использование в игровом цикле
output = MyUIOutput()
await game_loop(client, output)
```

## Протокол сообщений

### Подключение:
1. Клиент → Сервер: `{"type": "connect", "payload": {"player_name": "Name", "version": "1.0"}}`
2. Клиент → Сервер: `{"type": "lobby_ready", "payload": {}}`
3. Сервер → Клиент: `{"type": "room_list", "payload": {"rooms": [...]}}`

### Создание комнаты:
```json
{
  "type": "room_create",
  "payload": {
    "name": "My Room",
    "board_size": 19,
    "password": null,
    "komi": 6.5,
    "rules": "japanese"
  }
}
```

### Ход:
```json
{
  "type": "game_move",
  "payload": {
    "x": 3,
    "y": 4,
    "move_number": 5
  }
}
```

## Структура файлов

```
network_pvp/
├── protocol.py          # Типы сообщений и протокол
├── server.py            # WebSocket сервер
├── client.py            # Клиентская библиотека
├── console_network.py   # Консольный клиент
├── output_interface.py  # Независимый интерфейс вывода
└── readme.md           # Эта документация
```

## Зависимости

- Python 3.8+
- websockets>=16.0
- go_engine (через core_adapter)