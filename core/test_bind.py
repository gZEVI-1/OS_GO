import go_engine as go

# Создание игры 19x19
game = go.Game(19)

# Получение доски
board = game.get_board()
print(f"Board size: {board.get_size()}")

# Ход черных в точку (3, 3)
game.make_move(3, 3, False)  # x=3, y=3, is_pass=False

# Ход белых
game.make_move(15, 15, False)

# Пас
game.make_move(0, 0, True)

# Отмена хода
game.undo_last_move()

# Получение SGF
sgf = game.get_sgf()
print(sgf)

# Сохранение в файл
game.save_game("game.sgf")

# Работа с цветами
 # White

# Позиции
pos = go.Position(3, 3)
print(pos.x, pos.y)