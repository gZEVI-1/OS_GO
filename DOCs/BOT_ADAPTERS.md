# Документация: Адаптеры и анализаторы ИИ-ботов (OS-GO)

## Содержание
1. [Обзор архитектуры ИИ-подсистемы](#1-обзор-архитектуры-ии-подсистемы)
2. [GNU Go — адаптер и анализатор](#2-gnu-go--адаптер-и-анализатор)
3. [KataGo — адаптер и анализатор](#3-katago--адаптер-и-анализатор)
4. [Сравнение ботов](#4-сравнение-ботов)
5. [Интеграция с игровой сессией](#5-интеграция-с-игровой-сессией)
6. [Поток данных](#6-поток-данных)
7. [Расширение и кастомизация](#7-расширение-и-кастомизация)

---

## 1. Обзор архитектуры ИИ-подсистемы

Проект OS-GO поддерживает два ИИ-движка:
- **GNU Go** — классический бот, играет через GTP (Go Text Protocol), анализирует через подпроцессы
- **KataGo** — современный нейросетевой движок, анализирует через C++ биндинги (`go_engine`)

### Структура модулей

```
gnugo_adapter.py          # GTP-адаптер для GNU Go (игра + базовый анализ)
GnuGo_Analyzer.py         # Продвинутый анализатор GNU Go (подсчёт, парсинг)
KataGoAdapter.py          # Высокоуровневый адаптер для KataGo (анализ сессий)
KataGoAnalyzer.py         # Python-обёртка над C++ KataGoAnalyzer (go_engine)
```

### Роли в проекте

| Модуль | Назначение | Используется в |
|--------|-----------|----------------|
| `gnugo_adapter.py` | PvE-игра против бота, GTP-команды | `core_adapter.py` (`GameSession`) |
| `GnuGo_Analyzer.py` | Подсчёт очков, определение победителя | `server.py` (сетевые игры), `console_back.py` |
| `KataGoAnalyzer.py` | Нейросетевой анализ позиций | `KataGoAdapter.py` |
| `KataGoAdapter.py` | Интеграция анализа в игровую сессию | `console_back.py` (тесты) |

---

## 2. GNU Go — адаптер и анализатор

### 2.1 GNUGoBot (`gnugo_adapter.py`)

Класс-адаптер для управления GNU Go через **GTP (Go Text Protocol)**. Запускает GNU Go как подпроцесс и обменивается командами через stdin/stdout.

#### Инициализация

```python
from gnugo_adapter import GNUGoBot

bot = GNUGoBot(
    gnugo_path="bot/gnugo-3.8/gnugo.exe",
    board_size=19,
    komi=6.5,
    rules="chinese"  # или "japanese"
)
```

#### Жизненный цикл

```
[Создание] → start() → [Игра] → stop()
                ↓
         boardsize, clear_board, komi, set_rules
```

#### Методы

| Метод | Описание | GTP-команда |
|-------|----------|-------------|
| `start()` | Запуск процесса, инициализация доски | `boardsize N`, `clear_board`, `komi N`, `set_rules` |
| `stop()` | Корректное завершение (`quit` → terminate → kill) | `quit` |
| `play_move(color, x, y, is_pass)` | Передача хода боту | `play B/W <coord>` или `play B/W pass` |
| `get_move(color)` | Получение хода от бота | `genmove B/W` |
| `is_alive()` | Проверка жизни процесса | — |

#### Пример использования (PvE)

```python
bot = GNUGoBot("gnugo.exe", board_size=9)
if bot.start():
    # Человек сходил D4
    bot.play_move("B", 3, 3)  # GTP: play B d4

    # Получаем ответ бота
    move = bot.get_move("W")  # GTP: genmove W
    # move = {'is_pass': False, 'x': 4, 'y': 4}

    bot.stop()
```

#### Платформенные особенности

- **Windows:** использует `subprocess.CREATE_NO_WINDOW` для скрытия консоли
- **Linux/macOS:** стандартный `subprocess.Popen`
- **Координаты GTP:** буква + число (`D4`), буква `I` пропускается
- **Конвертация:** `_index_to_letter()` / `_letter_to_index()` — пропуск `I` (стандарт Го)

### 2.2 CoordinateUtils (`gnugo_adapter.py`)

Утилиты для работы с координатами Го:

```python
CoordinateUtils.index_to_letter(0)   # -> "A"
CoordinateUtils.index_to_letter(8)   # -> "J" (I пропущена)
CoordinateUtils.letter_to_index("J") # -> 8

CoordinateUtils.parse_move("D4", 19)  # -> {'x': 3, 'y': 3, 'is_pass': False, ...}
CoordinateUtils.parse_move("pass", 19) # -> {'is_pass': True, ...}
CoordinateUtils.parse_move("quit", 19) # -> {'quit': True, ...}
CoordinateUtils.parse_move("undo", 19) # -> {'undo': True, ...}

CoordinateUtils.format_move(3, 3)     # -> "D4"
```

### 2.3 PlayerType (`gnugo_adapter.py`)

```python
class PlayerType(Enum):
    HUMAN = auto()
    GNU_GO = auto()
```

Используется в `GameSession` (`core_adapter.py`) для определения типа игрока.

### 2.4 GnuGoAnalyzer (`GnuGo_Analyzer.py`)

Продвинутый анализатор для подсчёта очков и определения победителя. Работает через **временные файлы** и **pipe-перенаправление команд**.

#### Архитектура

```
SGF-строка → [временный .sgf файл] → [файл команд] → pipe → GNU Go --mode gtp
                                               ↓
                                         stdout → парсинг → результат
```

#### Инициализация

```python
from GnuGo_Analyzer import GnuGoAnalyzer

analyzer = GnuGoAnalyzer("bot/gnugo-3.8/gnugo.exe")
```

#### Методы

| Метод | Описание | Команды GNU Go |
|-------|----------|----------------|
| `analyze_sgf(sgf, board_size)` | Подсчёт финального счёта | `loadsgf`, `final_score` |
| `get_detailed_scores(sgf, board_size)` | Детальный анализ с оценкой | `loadsgf`, `estimate_score`, `final_score` |
| `cleanup()` | Удаление временных файлов | — |

#### Формат результата (`analyze_sgf`)

```python
{
    'winner': "Черные" | "Белые" | "Ничья",
    'winner_color': "B" | "W" | None,
    'margin': 12.5,           # разница в очках
    'full_result': "B+12.5"   # SGF-формат
}
```

#### Парсинг вывода

Регулярные выражения для извлечения результата:
- `B+12.5` → чёрные победили с отрывом 12.5
- `W+3.5` → белые победили с отрывом 3.5
- `0` или `jigo` → ничья

#### Вспомогательные функции

```python
# Быстрая проверка доступности
check_gnugo_available(gnugo_path) -> bool

# Определение победителя (1=чёрные, 2=белые, 0=ничья, -1=ошибка)
get_winner(sgf_content, board_size=19) -> int

# Полный подсчёт очков
get_score(sgf_content, board_size=19) -> dict
# {'black': X, 'white': Y, 'diff': Z, 'winner': 1|2|0, 'komi': 6.5}

# Упрощённый результат (+X чёрные, -X белые, 0 ничья)
get_score_simple(sgf_content, board_size=19) -> float
```

#### Платформенные особенности

- **Windows:** использует `type file.txt | gnugo.exe` (cmd pipe)
- **Linux/macOS:** аналогично через `cat`
- **Временные файлы:** создаются в `%TEMP%/TEMP_gnugo_analysis/`
- **Параметры:** `--mode gtp --boardsize N --chinese-rules --capture-all-dead --komi 6.5`

---

## 3. KataGo — адаптер и анализатор

### 3.1 KataGoAnalyzer (`KataGoAnalyzer.py`)

Python-обёртка над **C++ KataGoAnalyzer** из `go_engine`. Предоставляет нейросетевой анализ позиций.

#### Архитектура

```
Python KataGoAnalyzer
    └── self._cpp = go_engine.KataGoAnalyzer()  # C++ объект
```

#### Инициализация

```python
from KataGoAnalyzer import KataGoAnalyzer, KataGoAnalysisResult

analyzer = KataGoAnalyzer()
if analyzer.initialize():
    result = analyzer.analyze_sgf(sgf_content, board_size=19, komi=6.5)
```

#### Методы

| Метод | Описание |
|-------|----------|
| `initialize()` | Инициализация C++ движка (загрузка модели) |
| `analyze_sgf(sgf, board_size, komi)` | Анализ позиции |
| `cleanup()` / `shutdown()` | Освобождение ресурсов |

#### Формат результата (`KataGoAnalysisResult`)

```python
@dataclass
class KataGoAnalysisResult:
    success: bool = False
    winner: str = ""              # "Черные" | "Белые"
    margin: float = 0.0           # |score_lead|
    full_result: str = ""         # "Черные +X.X"
    black_score: float = 0.0
    white_score: float = 0.0
    winrate: float = 0.5          # вероятность победы чёрных
    best_move: str = ""           # лучший ход (координаты)
    top_moves: List[str] = []     # топ-5 рекомендаций
    error_message: str = ""
```

#### Конвертация из C++

```python
# C++ результат → Python dataclass
cpp_result = self._cpp.analyze_sgf(sgf, board_size, komi)

result.winner = "Черные" if cpp_result.winner == "Black" else "Белые"
result.margin = abs(cpp_result.score_lead)
result.winrate = cpp_result.winrate
result.best_move = cpp_result.best_move
result.top_moves = list(cpp_result.top_moves)
```

#### Вспомогательные функции

```python
# Проверка доступности (автоопределение путей)
is_available() -> bool

# Ручная установка путей
set_paths(katago_path, model_path, config_path="")

# Однострочный анализ
quick_analyze(sgf_content) -> Optional[KataGoAnalysisResult]
```

### 3.2 KataGoGameAnalyzer (`KataGoAdapter.py`)

Высокоуровневый адаптер для интеграции KataGo-анализа в **игровую сессию**.

#### Архитектура

```
KataGoGameAnalyzer
├── session: GameSession          # ссылка на игровую сессию
├── _analyzer: KataGoAnalyzer     # экземпляр анализатора
└── _initialized: bool
```

#### Методы

| Метод | Описание |
|-------|----------|
| `initialize()` | Создание `KataGoAnalyzer`, вызов `initialize()` |
| `analyze_current_game()` | Получение SGF из сессии → анализ |
| `print_analysis(result)` | Форматированный вывод в консоль |
| `cleanup()` | Освобождение ресурсов |

#### Контекстный менеджер

```python
with KataGoGameAnalyzer(session) as analyzer:
    if analyzer.initialize():
        result = analyzer.analyze_current_game()
        analyzer.print_analysis(result)
```

#### Интеграция в GameSession

```python
from KataGoAdapter import add_katago_analysis_to_session

# Добавляет автоматический анализ после окончания игры
add_katago_analysis_to_session(session, on_analysis_complete=custom_callback)
```

**Механизм:**
1. Сохраняет оригинальные `game_over_callbacks`
2. Добавляет свой callback первым
3. При `game_over` → запускает анализ → выводит результаты → вызывает оригинальные callbacks

---

## 4. Сравнение ботов

| Характеристика | GNU Go | KataGo |
|----------------|--------|--------|
| **Тип движка** | Классический (Monte Carlo + эвристики) | Нейросеть (ResNet + MCTS) |
| **Протокол** | GTP (подпроцесс) | C++ API (`go_engine`) |
| **Игра** | ✅ Полноценная (PvE) | ❌ Только анализ |
| **Анализ** | ✅ Подсчёт очков | ✅ Подсчёт + winrate + лучшие ходы |
| **Скорость** | Средняя | Медленная (загрузка модели) |
| **Платформа** | Кроссплатформенный | Зависит от C++ биндингов |
| **Использование** | `GNUGoBot` | `KataGoAnalyzer` |
| **Подсчёт** | `GnuGoAnalyzer.analyze_sgf()` | `KataGoAnalyzer.analyze_sgf()` |

---

## 5. Интеграция с игровой сессией

### 5.1 GameSession + GNU Go (`core_adapter.py`)

```python
class GameSession:
    def __init__(self, board_size=19, komi=6.5, rules=go.Rules.Chinese):
        self.game = go.Game(board_size)      # C++ движок
        self.gnugo_bot: Optional[GNUGoBot] = None
        self.players: Dict[go.Color, Dict]   # name, type, gtp_color
```

**Запуск PvE:**
```python
session = create_pve_session(
    board_size=19,
    player_color=go.Color.Black,
    player_name="Игрок",
    gnugo_path="bot/gnugo-3.8/gnugo.exe"
)
session.start()  # Создаёт GNUGoBot, запускает процесс
```

**Ход игрока → синхронизация с ботом:**
```python
# 1. Игрок делает ход
session.make_move(x, y)  # или session.make_human_move("D4")

# 2. C++ движок обновляет доску
# 3. Если есть gnugo_bot — отправляем ход в GNU Go
self.gnugo_bot.play_move(gtp_color, x, y, is_pass)

# 4. Если следующий игрок — бот
if players[next]['type'] == PlayerType.GNU_GO:
    session._make_bot_move()  # get_move() → make_move()
```

**Отмена хода:**
```python
session.undo_move()
# 1. C++ undo_last_move()
# 2. Перезапуск GNU Go (stop → start)
# 3. Воспроизведение всех ходов из SGF в бота
```

### 5.2 GameSession + KataGo (`KataGoAdapter.py`)

```python
# Автоматический анализ после игры
add_katago_analysis_to_session(session)

# При game_over:
# 1. session.game.get_sgf() → SGF-строка
# 2. KataGoAnalyzer.analyze_sgf(sgf, size, komi)
# 3. Вывод: победитель, счёт, winrate, лучшие ходы
```

### 5.3 Сетевая игра + GNU Go Analyzer (`server.py`)

```python
# При завершении сетевой игры:
room.calculate_score()
# 1. Поиск gnugo в PATH / стандартных локациях
# 2. Создание GnuGoAnalyzer(gnugo_path)
# 3. analyzer.analyze_sgf(session.game.get_sgf(), board_size)
# 4. Определение победителя для GAME_OVER
```

---

## 6. Поток данных

### 6.1 PvE-игра против GNU Go

```
[Игрок] → "D4" → GameSession.make_human_move()
              ↓
    CoordinateUtils.parse_move("D4", 19) → {'x': 3, 'y': 3}
              ↓
    go.Game.make_move(3, 3)  [C++ движок]
              ↓
    GNUGoBot.play_move("B", 3, 3)  [GTP: play B d4]
              ↓
    [Проверка game_over] → Нет
              ↓
    Следующий игрок = GNU Go
              ↓
    _make_bot_move():
        GNUGoBot.get_move("W")  [GTP: genmove W]
              ↓
        go.Game.make_move(bot_x, bot_y)
              ↓
    [Проверка game_over] → Да
              ↓
    _notify_game_over() → save_game() → SGF
```

### 6.2 Анализ завершённой игры (GNU Go)

```
[SGF-строка] → GnuGoAnalyzer.analyze_sgf()
              ↓
    [Временный файл game.sgf]
    [Файл команд: loadsgf → final_score → quit]
              ↓
    subprocess: type commands.txt | gnugo.exe --mode gtp ...
              ↓
    stdout: "= B+12.5"
              ↓
    _parse_gnugo_output() → {'winner': 'Черные', 'margin': 12.5}
              ↓
    cleanup() → удаление временных файлов
```

### 6.3 Анализ завершённой игры (KataGo)

```
[GameSession] → game.get_sgf() → SGF-строка
              ↓
    KataGoGameAnalyzer.analyze_current_game()
              ↓
    KataGoAnalyzer.analyze_sgf(sgf, 19, 6.5)
              ↓
    C++: go.KataGoAnalyzer.analyze_sgf()  [нейросеть]
              ↓
    KataGoAnalysisResult:
        winner="Черные", margin=5.3,
        winrate=0.72, best_move="Q16",
        top_moves=["Q16", "D4", "C16", ...]
              ↓
    print_analysis() → консольный вывод
```

### 6.4 Сетевая игра — подсчёт очков

```
[Сервер] GAME_OVER (два паса)
              ↓
    GameRoom._finalize_game()
              ↓
    GameRoom.calculate_score()
              ↓
    [Поиск gnugo в PATH]
              ↓
    GnuGoAnalyzer(gnugo_path).analyze_sgf(sgf, board_size)
              ↓
    [Результат: winner, margin]
              ↓
    Message.game_over(winner, result, sgf)
              ↓
    [Все клиенты] → отображение результата
```

---

## 7. Расширение и кастомизация

### 7.1 Добавление нового GTP-бота

```python
class NewBotAdapter:
    def __init__(self, path, board_size, komi):
        self.process = subprocess.Popen([path, "--gtp"], ...)

    def start(self): ...
    def play_move(self, color, x, y, is_pass): ...
    def get_move(self, color) -> Optional[Dict]: ...
    def stop(self): ...
```

Затем в `GameSession`:
```python
class PlayerType(Enum):
    HUMAN = auto()
    GNU_GO = auto()
    NEW_BOT = auto()  # добавить
```

### 7.2 Кастомный анализатор

```python
class CustomAnalyzer:
    def analyze_sgf(self, sgf, board_size) -> Dict:
        # Своя логика подсчёта
        return {'winner': ..., 'margin': ...}
```

### 7.3 Интеграция KataGo в сетевую игру

Для анализа партий в реальном времени:
```python
# В NetworkClient или QtNetworkClient:
def analyze_position(self):
    board = self.get_local_board()  # go.Board из состояния
    sgf = board.to_sgf()
    result = KataGoAnalyzer().analyze_sgf(sgf, self.board_size, self.komi)
    return result.best_move, result.winrate
```

---

## Приложение A: Зависимости

```
# GNU Go
- gnugo-3.8/gnugo.exe (Windows) или gnugo (Linux)
- subprocess (стандартная библиотека)
- tempfile, shutil (для GnuGoAnalyzer)

# KataGo
- go_engine.KataGoAnalyzer (C++ биндинги)
- Модель нейросети (автоопределение путей)
```

## Приложение B: Пути по умолчанию

```
# GNU Go (Windows)
bot/gnugo-3.8/gnugo.exe

# GNU Go (Linux)
gnugo

# KataGo (автоопределение)
bot/KataGo-1.16.4-OpenCL/katago.exe
bot/katago/katago.exe
```

## Приложение C: GTP-команды

| Команда | Описание |
|---------|----------|
| `boardsize N` | Установка размера доски |
| `clear_board` | Очистка доски |
| `komi N` | Установка коми |
| `set_rules chinese/japanese` | Правила подсчёта |
| `play B/W <coord>` | Передача хода |
| `genmove B/W` | Запрос хода |
| `loadsgf <file>` | Загрузка SGF |
| `final_score` | Финальный подсчёт |
| `estimate_score` | Оценка позиции |
| `quit` | Завершение |
