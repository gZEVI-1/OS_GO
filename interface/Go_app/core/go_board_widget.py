import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PySide6.QtCore import Qt, QRect, QPoint, Signal
import sys
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(root_path / "scripts"))

import go_engine as go

class GoBoardWidget(QWidget):
    cell_clicked = Signal(int, int)
    move_made = Signal(int, int, int)
    game_over = Signal(int)
    invalid_move = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent) 
        self.board_size = 9
        self.margin = 20
        self.cell_size = 0
        self.board_state = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.last_move = None
        self.current_player = 1
        self.core_api = None
        self.board_color = QColor(222, 184, 135)
        self.line_color = Qt.black
        self.black_stone_color = QColor(30, 30, 30)
        self.white_stone_color = Qt.white
        self.highlight_color = QColor(255, 0, 0, 100)
        self.offset_x = self.margin
        self.offset_y = self.margin
        self.flipped = False
        
        # Настройки подсказок
        self.show_legal_moves = True
        self.legal_moves = []
        
        self.update_cell_size()

    def set_board_size(self, size):
        """Устанавливает размер доски"""
        self.board_size = size
        self.board_state = [[0 for _ in range(size)] for _ in range(size)]
        self.update_cell_size()
        self.update_legal_moves()  # Обновляем после изменения размера
        self.update()

    def set_core_api(self, core_api):
        """Устанавливает API игры"""
        self.core_api = core_api
        if self.core_api:
            self.update_from_core()

    def update_legal_moves(self):
        """Обновление списка допустимых ходов"""
        if not self.show_legal_moves or self.core_api is None:
            self.legal_moves = []
            return
        
        self.legal_moves = []
        
        try:
            # Получаем объект Board с допустимыми ходами
            legal_board = self.core_api.get_legal_moves()
            
            if legal_board is not None and hasattr(legal_board, 'get_board_array'):
                board_array = legal_board.get_board_array()
                
                # Проходим по всем клеткам
                for row in range(self.board_size):
                    for col in range(self.board_size):
                        # Если в legal_board значение != 0, значит ход допустим
                        if board_array and board_array[col][row] != 0:
                            if self.board_state and self.board_state[row][col] == 0:
                                self.legal_moves.append((row, col))
                                
        except Exception:
            pass  # Игнорируем ошибки
    def update_from_core(self):
        """Обновление состояния доски из core API"""
        if not self.core_api:
            return
            
        try:
            board = self.core_api.get_board()
            raw_board = board.get_board_array()
            
            # Синхронизируем размер если нужно
            if len(raw_board) != self.board_size:
                self.set_board_size(len(raw_board))
            
            self.board_state = [
                [raw_board[x][y] for x in range(self.board_size)]
                for y in range(self.board_size)
            ]
            
            # Получаем текущего игрока
            player = self.core_api.get_current_player()
            self.current_player = 1 if player == go.Color.Black else 2
            
            # Обновляем список допустимых ходов
            self.update_legal_moves()
        except Exception as e:
            print(f"Ошибка при обновлении доски: {e}")
        
        self.update()

    def mousePressEvent(self, event):
        if self.core_api is None:
            return

        pos = event.position().toPoint()
        x = pos.x() - self.offset_x
        y = pos.y() - self.offset_y

        if x < 0 or y < 0:
            return

        screen_col = round(x / self.cell_size)
        screen_row = round(y / self.cell_size)

        if 0 <= screen_row < self.board_size and 0 <= screen_col < self.board_size:
            # Преобразуем экранные координаты в логические (для сервера)
            if self.flipped:
                logical_row = self.board_size - 1 - screen_row
                logical_col = self.board_size - 1 - screen_col
            else:
                logical_row = screen_row
                logical_col = screen_col
            self.cell_clicked.emit(logical_row, logical_col)

    def request_move(self, row, col):
        """Запрос на выполнение хода"""
        if not self.core_api:
            return False
        
        player = self.current_player
        success = self.core_api.make_move(col, row, False)
        
        if success:
            self.last_move = (row, col)
            self.update_from_core()
            self.move_made.emit(row, col, player)
            return True
        else:
            self.invalid_move.emit(row, col)
            return False

    def pass_move(self):
        """Пас"""
        if not self.core_api:
            return False
        success = self.core_api.make_move(0, 0, True)
        if success:
            self.update_from_core()
            return True
        return False

    def resizeEvent(self, event):
        self.update_cell_size()
        self.update()
        super().resizeEvent(event)

    def update_cell_size(self):
        if self.board_size > 1:
            available_width = self.width() - 2 * self.margin
            available_height = self.height() - 2 * self.margin

            if available_width > 0 and available_height > 0:
                max_cell_by_width = available_width // (self.board_size - 1)
                max_cell_by_height = available_height // (self.board_size - 1)
                self.cell_size = min(max_cell_by_width, max_cell_by_height)

                grid_size = (self.board_size - 1) * self.cell_size
                self.offset_x = (self.width() - grid_size) // 2
                self.offset_y = (self.height() - grid_size) // 2
            else:
                self.cell_size = 30
                self.offset_x = self.margin
                self.offset_y = self.margin
        else:
            self.cell_size = 30
            self.offset_x = self.margin
            self.offset_y = self.margin

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.board_color)
        self.draw_grid(painter)
        
        # Рисуем подсказки ПЕРЕД камнями
        if self.show_legal_moves and self.legal_moves:
            self.draw_move_hints(painter)
        
        if self.board_state:
            self.draw_stones(painter)
        self.draw_last_move_highlight(painter)
    
    def draw_last_move_highlight(self, painter):
        if self.last_move:
            logical_row, logical_col = self.last_move
            # Преобразуем логические координаты в экранные
            if self.flipped:
                screen_row = self.board_size - 1 - logical_row
                screen_col = self.board_size - 1 - logical_col
            else:
                screen_row = logical_row
                screen_col = logical_col

            x = self.offset_x + screen_col * self.cell_size
            y = self.offset_y + screen_row * self.cell_size
            painter.setBrush(QBrush(self.highlight_color))
            painter.setPen(Qt.NoPen)
            radius = self.cell_size // 2 + 4
            painter.drawEllipse(QPoint(x, y), radius, radius)

    def draw_grid(self, painter):
        painter.setPen(QPen(self.line_color, 1))
        start_x = self.offset_x
        start_y = self.offset_y
        end_x = start_x + (self.board_size - 1) * self.cell_size
        end_y = start_y + (self.board_size - 1) * self.cell_size

        for i in range(self.board_size):
            x = start_x + i * self.cell_size
            painter.drawLine(x, start_y, x, end_y)
            y = start_y + i * self.cell_size
            painter.drawLine(start_x, y, end_x, y)

        self.draw_hoshi(painter)

    def draw_hoshi(self, painter):
        painter.setBrush(Qt.black)
        painter.setPen(Qt.NoPen)

        hoshi_logical = {
            9: [(2, 2), (6, 2), (4, 4), (2, 6), (6, 6)],
            13: [(3, 3), (9, 3), (6, 6), (3, 9), (9, 9)],
            19: [(3, 3), (15, 3), (3, 15), (15, 15), (9, 9),
                (3, 9), (9, 3), (15, 9), (9, 15)]
        }

        if self.board_size in hoshi_logical:
            for logical_row, logical_col in hoshi_logical[self.board_size]:
                # Преобразуем логические координаты в экранные
                if self.flipped:
                    screen_row = self.board_size - 1 - logical_row
                    screen_col = self.board_size - 1 - logical_col
                else:
                    screen_row = logical_row
                    screen_col = logical_col
                x = self.offset_x + screen_col * self.cell_size
                y = self.offset_y + screen_row * self.cell_size
                painter.drawEllipse(QPoint(x, y), 4, 4)

    def draw_stones(self, painter):
        for screen_row in range(self.board_size):
            for screen_col in range(self.board_size):
                # Определяем логические координаты (в массиве)
                if self.flipped:
                    logical_row = self.board_size - 1 - screen_row
                    logical_col = self.board_size - 1 - screen_col
                else:
                    logical_row = screen_row
                    logical_col = screen_col

                stone = self.board_state[logical_row][logical_col] if 0 <= logical_row < self.board_size and 0 <= logical_col < self.board_size else 0
                if stone == 0:
                    continue

                x = self.offset_x + screen_col * self.cell_size
                y = self.offset_y + screen_row * self.cell_size

                if stone == 1:
                    painter.setBrush(QBrush(self.black_stone_color))
                else:
                    painter.setBrush(QBrush(self.white_stone_color))

                radius = self.cell_size // 2 - 2
                painter.setPen(QPen(Qt.gray, 1))
                painter.drawEllipse(QRect(x - radius, y - radius, radius * 2, radius * 2))

    def draw_move_hints(self, painter):
        painter.setBrush(QBrush(QColor(150, 150, 150, 80)))
        painter.setPen(Qt.NoPen)
        radius = self.cell_size // 6

        for logical_row, logical_col in self.legal_moves:
            if self.flipped:
                screen_row = self.board_size - 1 - logical_row
                screen_col = self.board_size - 1 - logical_col
            else:
                screen_row = logical_row
                screen_col = logical_col

            x = self.offset_x + screen_col * self.cell_size
            y = self.offset_y + screen_row * self.cell_size
            painter.drawEllipse(QPoint(x, y), radius, radius)
    
    def set_flipped(self, flipped: bool):
        if self.flipped != flipped:
            self.flipped = flipped
            self.update()

    def set_board_state(self, board_array, last_move=None):
        self.board_state = board_array
        self.last_move = last_move
        self.update()