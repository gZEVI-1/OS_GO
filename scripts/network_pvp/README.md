# OS-GO Network PvP Module

Клиент-серверная реализация для сетевой игры в Го через лобби.

## Архитектура

```
network_pvp/
├── protocol.py              # Общий протокол сообщений
├── server.py                 # WebSocket сервер (FastAPI)
├── client.py                 # Консольный клиент
├── console_pvp_network.py    # Интеграция с существующей системой
├── config.py                 # Конфигурация
├── gui_integration_example.py # Пример PySide6 интеграции
├── test_protocol.py          # Тесты протокола
├── demo.py                   # Демо-скрипт
├── requirements.txt          # Зависимости
├── Dockerfile                # Docker образ
├── docker-compose.yml        # Docker Compose
├── .env.example              # Пример конфигурации
└── README.md                 # Документация
```

## Компоненты

### 1. protocol.py — Протокол обмена

**Назначение**: Единый формат сообщений между клиентом и сервером.

**Ключевые классы**:
- `MessageType` — перечисление всех типов сообщений
- `GameSettings` — настройки партии (размер доски, правила, коми)
- `PlayerInfo` — публичная информация об игроке
- `RoomInfo` — информация о комнате для лобби
- `MessageBuilder` — сериализация/десериализация JSON
- `Messages` — готовые шаблоны сообщений

**Типы сообщений**:

| Тип | Направление | Описание |
|-----|-------------|----------|
| `connect` | C→S | Подключение с авторизацией |
| `connected` | S→C | Подтверждение подключения |
| `create_room` | C→S | Создание комнаты |
| `room_created` | S→C | Комната создана |
| `join_room` | C→S | Вход в комнату |
| `room_joined` | S→C | Успешный вход |
| `ready` | C→S | Готовность к игре |
| `game_start` | S→C | Начало партии |
| `make_move` | C→S | Ход игрока |
| `move_made` | S→C | Подтверждение хода |
| `pass` | C→S | Пас |
| `resign` | C→S | Сдача |
| `game_over` | S→C | Конец партии |
| `chat` | ↔ | Сообщение чата |
| `sync_request` | C→S | Запрос синхронизации |
| `sync_state` | S→C | Полное состояние |

### 2. server.py — Сервер

**Назначение**: Центральный сервер для управления комнатами и игровым состоянием.

**Запуск**:
```bash
# Установка зависимостей
pip install fastapi uvicorn websockets

# Запуск сервера
uvicorn server:app --host 0.0.0.0 --port 8765 --reload
```

**Эндпоинты**:
- `GET /` — Health check
- `GET /rooms` — Список комнат (HTTP)
- `WS /ws` — Основной WebSocket endpoint

**Классы**:
- `RoomManager` — управление комнатами (создание, вход, выход, broadcast)
- `Room` — состояние комнаты
- `GameState` — серверное состояние партии (авторитетное)
- `PlayerConnection` — обёртка WebSocket соединения

**Особенности**:
- Авторитетный сервер: все ходы валидируются сервером
- Поддержка реконнекта через `sync_request`
- Автоматическая очистка пустых комнат
- Готов к масштабированию через Redis Pub/Sub

### 3. client.py — Консольный клиент

**Назначение**: Игровой клиент для консольного режима.

**Запуск**:
```bash
# Подключение к локальному серверу
python client.py

# Подключение к удалённому серверу
python client.py ws://192.168.1.100:8765/ws

# С указанием имени
python client.py ws://server.com:8765/ws -u PlayerName
```

**Управление в лобби**:
```
1 — Создать комнату
2 — Войти в комнату
3 — Список комнат
4 — Обновить
q — Выход
```

**Управление в игре**:
```
d4      — Ход на пересечение D4
pass    — Пас
resign  — Сдаться
chat <текст> — Сообщение в чат
save    — Сохранить SGF
help    — Помощь
quit    — Выход
```

**Классы**:
- `NetworkClient` — основной клиент с обработкой состояний
- `ConsoleRenderer` — отрисовка доски и UI в консоли
- `ClientState` — состояния клиента (FSM)
- `GameData` — локальное зеркало игрового состояния

### 4. console_pvp_network.py — Интеграция

**Назначение**: Мост между сетевым клиентом и существующей архитектурой.

**Ключевые классы**:
- `NetworkPvPGame` — высокоуровневый контроллер с тем же интерфейсом, что и локальный PvP
- `NetworkGamePhase` — расширенные фазы сетевой игры
- `NetworkGameCallbacks` — callback-интерфейс для UI интеграции

**Интеграция с PySide6**:
```python
from PySide6.QtCore import QObject, Signal
from console_pvp_network import NetworkPvPGame, NetworkGameCallbacks

class NetworkGameBridge(QObject):
    moveMade = Signal(dict)
    gameStarted = Signal()
    opponentJoined = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.game = NetworkPvPGame()
        self.game.callbacks = NetworkGameCallbacks(
            on_move_made=self.moveMade.emit,
            on_game_started=self.gameStarted.emit,
            on_opponent_joined=self.opponentJoined.emit,
        )
    
    async def connect(self):
        return await self.game.initialize()
    
    async def makeMove(self, x, y):
        await self.game.make_move(x, y)
```

## Поток данных

```
┌─────────────┐     WebSocket      ┌─────────────┐
│   Client 1  │◄──────────────────►│   Server    │
│  (Black)    │                    │  (Authoritative)
└─────────────┘                    └──────┬──────┘
     │                                  │
     │         sync state               │
     │◄─────────────────────────────────┤
     │         make_move(x,y)           │
     ├─────────────────────────────────►│
     │         move_made(x,y)           │
     │◄─────────────────────────────────┤
     │         broadcast                │
     │◄─────────────────────────────────┤
     │                                  │
┌─────────────┐                    ┌──────┴──────┐
│   Client 2  │◄──────────────────►│   Room      │
│  (White)    │    move_made(x,y)    │   Manager   │
└─────────────┘                      └─────────────┘
```

## Инструкция по запуску

### 1. Запуск сервера

```bash
cd network_pvp
pip install -r requirements.txt

# Режим разработки
uvicorn server:app --host 0.0.0.0 --port 8765 --reload

# Продакшен
uvicorn server:app --host 0.0.0.0 --port 8765 --workers 4
```

### 2. Запуск клиента (Игрок 1 — создаёт комнату)

```bash
cd network_pvp
python client.py ws://localhost:8765/ws -u Alice

# В лобби:
# > 1 (Создать комнату)
# Введите название: Alice's Room
# Выберите размер: 3 (19x19)
# Выберите правила: 1 (Chinese)
# > ready
```

### 3. Запуск клиента (Игрок 2 — подключается)

```bash
# На другом ПК или в другом терминале
python client.py ws://<IP_сервера>:8765/ws -u Bob

# В лобби:
# > 2 (Войти в комнату)
# Введите ID комнаты: <ID из шага 2>
# > ready
```

### 4. Игра

```
[YOUR MOVE] > d4
[YOUR MOVE] > pass
[YOUR MOVE] > chat Привет!
[YOUR MOVE] > save
```

## Требования

```
Python >= 3.10
fastapi >= 0.100.0
uvicorn >= 0.23.0
websockets >= 11.0
```

## Масштабирование

Для поддержки множества серверов за балансировщиком:

1. **Redis Pub/Sub**: Заменить in-memory `RoomManager` на Redis-адаптер
2. **Sticky Sessions**: Настроить балансировщик для привязки сессий
3. **State Persistence**: Сохранять состояние комнат в PostgreSQL

Пример Redis-адаптера уже заложен в архитектуре `RoomManager`.

## Безопасность

- Все ходы валидируются сервером (авторитетный сервер)
- Поддержка паролей на комнаты
- JWT-токены для аутентификации (заготовка в `handle_connect`)
- Rate limiting на ходы (рекомендуется добавить)

## Лицензия

MIT License — часть проекта OS-GO.
