import os
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap
from PySide6.QtCore import Qt, QRect, QPoint, Signal
import go_engine as go

class GoBoardWidget(QWidget):
    cell_clicked = Signal(int, int)
    move_made = Signal(int, int, int)
    game_over = Signal(int)
    invalid_move = Signal(int, int)

    def __init__(self, parent=None):
            super().__init__(parent)
            self.setFixedSize(421, 421)
            self.board_size = 19
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
            self.update_cell_size()

    def set_core_api(self, core_api):
        self.core_api = core_api
        self.update_from_core()


    def set_board_size(self, size):
        self.board_size = size
        self.update_cell_size()
        if self.core_api:
            self.update_from_core()
        else:
            self.board_state = [[0 for _ in range(size)] for _ in range(size)]
        self.update()

    def update_cell_size(self):
        available_space = self.width() - 2 * self.margin
        self.cell_size = available_space // (self.board_size - 1)

    def resizeEvent(self, event):
        self.update_cell_size()
        self.update()
        super().resizeEvent(event)

    def update_from_core(self):
        if self.core_api:
            board = self.core_api.get_board()
            self.board_state = board.get_board_array()
            player = self.core_api.get_current_player()
            self.current_player = 1 if player == go.Color.Black else 2
        self.update()

    def mousePressEvent(self, event):
        pos = event.position().toPoint()
        col = round((pos.x() - self.margin) / self.cell_size)
        row = round((pos.y() - self.margin) / self.cell_size)
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            self.cell_clicked.emit(row, col)


    def request_move(self, row, col):
        if not self.core_api:
            return False
        
        player = self.current_player
        success = self.core_api.make_move(col, row, False)
        
        if success:
            self.last_move = (row, col)
            self.update_from_core()
            self.move_made.emit(row, col, player)
            
            if self.core_api.is_game_over():
                self.game_over.emit(0)  
            return True
        else:
            self.invalid_move.emit(row, col)
            return False

    def pass_move(self):
        if not self.core_api:
            return False
        success = self.core_api.make_move(0, 0, True)
        if success:
            self.update_from_core()
            return True
        return False
    

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.board_color)
        self.draw_grid(painter)
        if self.board_state:
            self.draw_stones(painter)
        self.draw_last_move_highlight(painter)

    def draw_grid(self, painter):
        painter.setPen(QPen(self.line_color, 1))
        start = self.margin
        end = self.margin + (self.board_size - 1) * self.cell_size
        for i in range(self.board_size):
            x = self.margin + i * self.cell_size
            painter.drawLine(x, start, x, end)
            y = self.margin + i * self.cell_size
            painter.drawLine(start, y, end, y)
        self.draw_hoshi(painter)

    def draw_hoshi(self, painter):
        painter.setBrush(Qt.black)
        painter.setPen(Qt.NoPen)
        hoshi_positions = {
            9:  [(2, 2), (6, 2), (4, 4), (2, 6), (6, 6)],
            13: [(3, 3), (9, 3), (6, 6), (3, 9), (9, 9)],
            19: [(3, 3), (15, 3), (3, 15), (15, 15), (9, 9),
                 (3, 9), (9, 3), (15, 9), (9, 15)]
        }
        if self.board_size in hoshi_positions:
            for row, col in hoshi_positions[self.board_size]:
                x = self.margin + col * self.cell_size
                y = self.margin + row * self.cell_size
                painter.drawEllipse(QPoint(x, y), 4, 4)

    def draw_stones(self, painter):
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board_state[row][col] != 0:
                    x = self.margin + col * self.cell_size
                    y = self.margin + row * self.cell_size
                    if self.board_state[row][col] == 1:
                        painter.setBrush(QBrush(self.black_stone_color))
                    else:
                        painter.setBrush(QBrush(self.white_stone_color))
                    radius = self.cell_size // 2 - 2
                    painter.setPen(QPen(Qt.gray, 1))
                    painter.drawEllipse(QRect(x - radius, y - radius,
                                              radius * 2, radius * 2))

    def draw_last_move_highlight(self, painter):
        if self.last_move:
            row, col = self.last_move
            x = self.margin + col * self.cell_size
            y = self.margin + row * self.cell_size
            painter.setBrush(QBrush(self.highlight_color))
            painter.setPen(Qt.NoPen)
            radius = self.cell_size // 2 + 4
            painter.drawEllipse(QPoint(x, y), radius, radius)
