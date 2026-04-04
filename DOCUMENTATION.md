
  * [Перечисления](#------------)
    + [`Color`](#-color-)
  * [Структуры данных](#----------------)
    + [`Position`](#-position-)
    + [`Move`](#-move-)
  * [Классы](#------)
    + [`Group`](#-group-)
      - [`contains(x: int, y: int) -> bool`](#-contains-x--int--y--int-----bool-)
      - [`add_stone(x: int, y: int) -> None`](#-add-stone-x--int--y--int-----none-)
      - [`remove_stone(x: int, y: int) -> None`](#-remove-stone-x--int--y--int-----none-)
      - [`empty() -> bool`](#-empty------bool-)
    + [`Board`](#-board-)
      - [`get_board_array() -> list[list[int]]`](#-get-board-array------list-list-int---)
      - [`get_size() -> int`](#-get-size------int-)
      - [`get_color(pos: Position) -> Color`](#-get-color-pos--position-----color-)
      - [`get_color(x: int, y: int) -> Color`](#-get-color-x--int--y--int-----color-)
      - [`add_stone(pos: Position, color: Color) -> bool`](#-add-stone-pos--position--color--color-----bool-)
      - [`add_stone(x: int, y: int, color: Color) -> bool`](#-add-stone-x--int--y--int--color--color-----bool-)
      - [`remove_stone(pos: Position) -> bool`](#-remove-stone-pos--position-----bool-)
      - [`remove_stone(x: int, y: int) -> bool`](#-remove-stone-x--int--y--int-----bool-)
      - [`simple_print() -> None`](#-simple-print------none-)
      - [`find_group_index(pos: Position) -> int`](#-find-group-index-pos--position-----int-)
    + [`SGFGame`](#-sgfgame-)
      - [`add_move(move: Move) -> None`](#-add-move-move--move-----none-)
      - [`set_player_names(black: str, white: str) -> None`](#-set-player-names-black--str--white--str-----none-)
      - [`set_result(result: str) -> None`](#-set-result-result--str-----none-)
      - [`pos_to_sgf(pos: Position) -> str`](#-pos-to-sgf-pos--position-----str-)
      - [`generate_sgf() -> str`](#-generate-sgf------str-)
      - [`save_to_file(filename: str) -> bool`](#-save-to-file-filename--str-----bool-)
      - [`get_moves() -> list[Move]`](#-get-moves------list-move--)
      - [`clear() -> None`](#-clear------none-)
    + [`Game`](#-game-)
      - [`is_ok(pos: Position, board: Board, player_color: Color) -> bool`](#-is-ok-pos--position--board--board--player-color--color-----bool-)
      - [`re_pos_moves(rele_board: Board, player_color: Color) -> Board`](#-re-pos-moves-rele-board--board--player-color--color-----board-)
      - [`get_legal_moves() -> Board`](#-get-legal-moves------board-)
      - [`record_move(x: int, y: int, is_pass: bool = False) -> None`](#-record-move-x--int--y--int--is-pass--bool---false-----none-)
      - [`undo_last_move() -> bool`](#-undo-last-move------bool-)
      - [`get_sgf() -> str`](#-get-sgf------str-)
      - [`save_game(filepath: str) -> bool`](#-save-game-filepath--str-----bool-)
      - [`make_move(x: int, y: int, is_pass: bool = False) -> bool`](#-make-move-x--int--y--int--is-pass--bool---false-----bool-)
      - [`is_game_over() -> bool`](#-is-game-over------bool-)
      - [`get_current_player() -> Color`](#-get-current-player------color-)
      - [`get_move_number() -> int`](#-get-move-number------int-)
      - [`get_passes() -> int`](#-get-passes------int-)
      - [`get_board() -> Board`](#-get-board------board-)
      - [`get_board_const() -> Board`](#-get-board-const------board-)
  * [Утилитарные функции](#-------------------)
    + [`get_opponent_color(color: Color) -> Color`](#-get-opponent-color-color--color-----color-)
- [Примечания по реализации](#примечания-по-реализации)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>


## Перечисления

### `Color`

Цвет камня или игрока.

Table

| Значение      | Описание      |
| :------------ | :------------ |
| `Color.None`  | Пустая клетка |
| `Color.Black` | Чёрный камень |
| `Color.White` | Белый камень  |


[↑ Наверх](#документация-go_engine)

---

## Структуры данных

### `Position`

Представляет координаты на доске.

**Конструкторы:**

- `Position()` — создаёт позицию (0, 0)
    
- `Position(x: int, y: int)` — создаёт позицию с заданными координатами
    

**Атрибуты:**

Table

|Атрибут|Тип|Описание|
|:--|:--|:--|
|`x`|`int`|Координата X (0 — левый край)|
|`y`|`int`|Координата Y (0 — верхний край)|

**Методы:**

Table

|Метод|Описание|
|:--|:--|
|`__eq__(other)`|Проверка равенства позиций|
|`__ne__(other)`|Проверка неравенства|
|`__lt__(other)`|Сравнение позиций (для сортировки)|
|`__repr__()`|Строковое представление: `<Position(x, y)>`|

[↑ Наверх](#документация-go_engine-v116)

---

### `Move`

Представляет один ход в партии.

**Конструкторы:**

- `Move()` — пустой ход
    
- `Move(x: int, y: int, color: Color, move_number: int)` — обычный ход
    
- `Move(color: Color, move_number: int)` — пас (пропуск хода)
    

**Атрибуты:**

Table

|Атрибут|Тип|Описание|
|:--|:--|:--|
|`pos`|`Position`|Координаты хода (-1, -1 для паса)|
|`color`|`Color`|Цвет игрока, сделавшего ход|
|`move_number`|`int`|Номер хода в партии|
|`is_pass`|`bool`|`True` если ход — пас|

[↑ Наверх](#документация-go_engine-v116)

---

## Классы

### `Group`

Группа связанных камней одного цвета с общими дамэ.

**Конструкторы:**

- `Group()` — пустая группа без цвета
    
- `Group(color: Color)` — группа заданного цвета
    

**Атрибуты:**

Table

|Атрибут|Тип|Описание|
|:--|:--|:--|
|`color`|`Color`|Цвет камней в группе|
|`stones`|`list[Position]`|Список позиций камней группы|
|`liberties`|`set[Position]`|Множество позиций дамэ (свободных точек вокруг группы)|

**Методы:**

#### `contains(x: int, y: int) -> bool`

Проверяет, содержит ли группа камень в позиции (x, y).

**Параметры:**

- `x`, `y` — координаты
    

**Возвращает:** `True` если камень найден в группе

[↑ Наверх](#документация-go_engine-v116)

---

#### `add_stone(x: int, y: int) -> None`

Добавляет камень в группу.

**Параметры:**

- `x`, `y` — координаты нового камня
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `remove_stone(x: int, y: int) -> None`

Удаляет камень из группы.

**Параметры:**

- `x`, `y` — координаты удаляемого камня
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `empty() -> bool`

Проверяет, пуста ли группа (нет камней).

**Возвращает:** `True` если группа не содержит камней

[↑ Наверх](#документация-go_engine-v116)

---

### `Board`

Игровая доска с логикой размещения камней и правил.

**Конструктор:**

- `Board(size: int)` — создаёт доску размером size×size
    

**Методы:**

#### `get_board_array() -> list[list[int]]`

Возвращает текущее состояние доски в виде 2D массива.

**Возвращает:** Массив размером size×size, где:

- `0` — пустая клетка
    
- `1` — чёрный камень
    
- `2` — белый камень
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_size() -> int`

Возвращает размер доски.

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_color(pos: Position) -> Color`

#### `get_color(x: int, y: int) -> Color`

Возвращает цвет камня в указанной позиции.

**Параметры:**

- `pos` — объект Position, или
    
- `x`, `y` — координаты
    

**Возвращает:** `Color.Black`, `Color.White` или `Color.None`

[↑ Наверх](#документация-go_engine-v116)

---

#### `add_stone(pos: Position, color: Color) -> bool`

#### `add_stone(x: int, y: int, color: Color) -> bool`

Размещает камень на доску с проверкой правил.

**Параметры:**

- `pos` или `x`, `y` — координаты
    
- `color` — цвет камня
    

**Возвращает:**

- `True` — ход выполнен успешно
    
- `False` — ход невозможен (клетка занята, правило ко, или самоубийство)
    

**Проверки:**

- Клетка должна быть пустой
    
- Нарушение правила ко запрещено
    
- Ход не должен приводить к самоубийству (группа без дамэ)
    

**Побочные эффекты:**

- Объединяет группы камней того же цвета
    
- Захватывает камни противника без дамэ
    
- Обновляет правило ко при захвате одного камня
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `remove_stone(pos: Position) -> bool`

#### `remove_stone(x: int, y: int) -> bool`

Удаляет камень с доски (вспомогательный метод).

**Параметры:**

- `pos` или `x`, `y` — координаты
    

**Возвращает:** `True` если камень был удалён

**Примечание:** Используется в основном для отмены ходов. Сбрасывает правило ко.

[↑ Наверх](#документация-go_engine-v116)

---

#### `simple_print() -> None`

Выводит доску в консоль в текстовом виде.

Формат: координаты и символы (`+` — пусто, `B` — чёрный, `W` — белый)

[↑ Наверх](#документация-go_engine-v116)

---

#### `find_group_index(pos: Position) -> int`

Находит индекс группы, содержащей камень в позиции.

**Параметры:**

- `pos` — позиция камня
    

**Возвращает:** Индекс группы или `-1` если камень не найден

[↑ Наверх](#документация-go_engine-v116)

---

### `SGFGame`

Управление SGF-записью партии (Smart Game Format).

**Конструкторы:**

- `SGFGame()` — стандартная доска 9×9
    
- `SGFGame(size: int)` — доска заданного размера (минимум 9)
    

**Методы:**

#### `add_move(move: Move) -> None`

Добавляет ход в запись.

**Параметры:**

- `move` — объект Move
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `set_player_names(black: str, white: str) -> None`

Устанавливает имена игроков.

**Параметры:**

- `black` — имя чёрного игрока
    
- `white` — имя белого игрока
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `set_result(result: str) -> None`

Устанавливает результат партии.

**Параметры:**

- `result` — строка результата (например, "B+5.5", "W+R", "Void")
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `pos_to_sgf(pos: Position) -> str`

Конвертирует позицию в SGF-координаты.

**Параметры:**

- `pos` — позиция на доске
    

**Возвращает:** Строку из 2 символов (например, "dd" для 4-4)

- Поддерживает координаты 0-25 (a-z) и 26-51 (A-Z)
    
- Возвращает пустую строку для паса (-1, -1)
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `generate_sgf() -> str`

Генерирует полную SGF-строку партии.

**Возвращает:** Строку в формате SGF с заголовком и всеми ходами

[↑ Наверх](#документация-go_engine-v116)

---

#### `save_to_file(filename: str) -> bool`

Сохраняет SGF в файл.

**Параметры:**

- `filename` — путь к файлу
    

**Возвращает:** `True` при успешном сохранении

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_moves() -> list[Move]`

Возвращает список всех ходов.

[↑ Наверх](#документация-go_engine-v116)

---

#### `clear() -> None`

Очищает список ходов.

[↑ Наверх](#документация-go_engine-v116)

---

### `Game`

Основной класс для управления игровым процессом.

**Конструктор:**

- `Game(size: int = 9)` — создаёт игру на доске заданного размера
    

**Методы:**

#### `is_ok(pos: Position, board: Board, player_color: Color) -> bool`

Проверяет, возможен ли ход в данной позиции.

**Параметры:**

- `pos` — проверяемая позиция
    
- `board` — состояние доски для проверки
    
- `player_color` — цвет игрока, делающего ход
    

**Возвращает:** `True` если ход легален (не занято, не ко, не самоубийство)

[↑ Наверх](#документация-go_engine-v116)

---

#### `re_pos_moves(rele_board: Board, player_color: Color) -> Board`

Вычисляет доску возможных ходов.

**Параметры:**

- `rele_board` — текущее состояние доски
    
- `player_color` — цвет игрока
    

**Возвращает:** Доску, где `Color.Black` отмечает легальные ходы, `Color.None` — нелегальные

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_legal_moves() -> Board`

Возвращает текущую доску легальных ходов для игрока, чей сейчас ход.

**Возвращает:** Ссылку на объект Board (изменения влияют на внутреннее состояние)

[↑ Наверх](#документация-go_engine-v116)

---

#### `record_move(x: int, y: int, is_pass: bool = False) -> None`

Записывает ход в историю и SGF.

**Параметры:**

- `x`, `y` — координаты (-1 для паса)
    
- `is_pass` — `True` если ход — пас
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `undo_last_move() -> bool`

Отменяет последний ход.

**Возвращает:** `True` если отмена выполнена, `False` если ходов нет

**Действия:**

- Удаляет камень с доски (если не пас)
    
- Восстанавливает историю ходов
    
- Пересоздаёт SGF-запись
    
- Меняет текущего игрока обратно
    
- Корректирует счётчик пасов
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_sgf() -> str`

Возвращает текущую SGF-запись партии.

[↑ Наверх](#документация-go_engine-v116)

---

#### `save_game(filepath: str) -> bool`

Сохраняет игру в SGF-файл.

**Параметры:**

- `filepath` — путь к файлу (создаёт директории при необходимости)
    

**Возвращает:** `True` при успешном сохранении

[↑ Наверх](#документация-go_engine-v116)

---

#### `make_move(x: int, y: int, is_pass: bool = False) -> bool`

Выполняет ход.

**Параметры:**

- `x`, `y` — координаты (или -1, -1 для паса)
    
- `is_pass` — `True` для паса
    

**Возвращает:**

- `True` — ход принят
    
- `False` — ход отклонён
    

**Логика:**

- При пасе: увеличивает счётчик пасов, при 2 пасах игра завершается
    
- При обычном ходе: размещает камень, сбрасывает счётчик пасов
    
- Переключает текущего игрока
    
- Обновляет доску легальных ходов
    

[↑ Наверх](#документация-go_engine-v116)

---

#### `is_game_over() -> bool`

Проверяет, завершена ли игра (два паса подряд).

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_current_player() -> Color`

Возвращает цвет игрока, чей сейчас ход.

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_move_number() -> int`

Возвращает номер текущего хода (начиная с 1).

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_passes() -> int`

Возвращает количество пасов подряд.

[↑ Наверх](#документация-go_engine-v116)

---

#### `get_board() -> Board`

#### `get_board_const() -> Board`

Возвращает текущее состояние доски.

- `get_board()` — возвращает изменяемую ссылку
    
- `get_board_const()` — константная версия
    

[↑ Наверх](#документация-go_engine-v116)

---

## Утилитарные функции

### `get_opponent_color(color: Color) -> Color`

Возвращает противоположный цвет.

Table

|Вход|Выход|
|:--|:--|
|`Color.Black`|`Color.White`|
|`Color.White`|`Color.Black`|
|`Color.None`|`Color.None`|


[↑ Наверх](#документация-go_engine-v116)

# Примечания по реализации

1. **Правило ко**: Реализовано корректно — запрещает немедленный возврат камня в точку захвата одного камня
    

2. **Самоубийство**: Запрещено — ход, после которого группа игрока остаётся без дамэ, отклоняется
    
3. **Координаты**:
    
    - Внутренние: 0-based (0,0 — левый верхний угол)
        
    - SGF: a-based (a,a — левый нижний угол в терминах Го, но здесь (0,0) → "aa")
        
4. **Размер доски**: Минимум 9×9 для SGF, но Board поддерживает любой размер
    
5. **Копирование**: Board поддерживает конструктор копирования и оператор присваивания


[↑ Наверх](#документация-go_engine-v116)
