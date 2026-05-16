#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OS-GO Network Client — Quick PySide6 GUI
========================================
Быстрый интерфейс для онлайн-игры в Го.
Запуск: python pyside6_go_client.py

Требования: PySide6, websockets
"""

import sys
import os
import asyncio
import threading
from typing import Optional, List, Dict, Any

from PySide6.QtCore import (
    Qt, QObject, Signal, QThread, QMetaObject, Q_ARG, QSize, QPoint, QRect
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QMouseEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QStackedWidget, QGridLayout, QFrame, QMessageBox, QInputDialog,
    QHeaderView, QSplitter, QSizePolicy, QDialog, QFormLayout, QSpinBox,
    QDoubleSpinBox, QComboBox, QDialogButtonBox, QFileDialog
)

# --- Пути к вашим модулям ---
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, SCRIPT_DIR)
# sys.path.insert(0, os.path.join(SCRIPT_DIR, '..'))

try:
    from client_ad import NetworkClient, ConnectionState
    from protocol_ad import Message, MessageType, RoomInfo
    from output_interface_ad import GameDisplayState
except ImportError as e:
    print(f"Ошибка импорта бэкенда: {e}")
    print("Убедитесь, что рядом лежат: client_ad.py, protocol_ad.py, output_interface_ad.py")
    sys.exit(1)


# ============================================================================
# 1. Поток с asyncio event loop (изолирует WebSocket от Qt)
# ============================================================================

class AsyncioThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = True

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        self._running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait(3000)

    def submit(self, coro):
        if self.loop and self._running and not self.loop.is_closed():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        return None


# ============================================================================
# 2. QObject-обёртка: asyncio-колбэки → Qt-сигналы
# ============================================================================

class QtNetworkClient(QObject):
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
    chat_message = Signal(str, str)              # sender, text
    undo_requested = Signal(str)               # requester name
    undo_responded = Signal(bool)              # accepted
    connection_state_changed = Signal(str)     # state name

    def __init__(self, server_url: str, player_name: str, parent=None):
        super().__init__(parent)
        self._client = NetworkClient(server_url, player_name)
        self._thread = AsyncioThread(self)
        self._thread.start()

        # Подключаем колбэки
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
        QMetaObject.invokeMethod(self, "connection_state_changed", Qt.QueuedConnection,
                                 Q_ARG(str, "connected"))

    def _emit_disconnected(self):
        QMetaObject.invokeMethod(self, "disconnected", Qt.QueuedConnection)
        QMetaObject.invokeMethod(self, "connection_state_changed", Qt.QueuedConnection,
                                 Q_ARG(str, "disconnected"))

    def _emit_error(self, code, msg):
        QMetaObject.invokeMethod(self, "error_occurred", Qt.QueuedConnection,
                                 Q_ARG(str, code), Q_ARG(str, msg))

    def _emit_room_list(self, rooms):
        QMetaObject.invokeMethod(self, "room_list_received", Qt.QueuedConnection,
                                 Q_ARG(list, rooms))

    def _emit_room_joined(self, rid, color):
        QMetaObject.invokeMethod(self, "room_joined", Qt.QueuedConnection,
                                 Q_ARG(str, rid), Q_ARG(str, color))

    def _emit_room_updated(self, payload):
        QMetaObject.invokeMethod(self, "room_updated", Qt.QueuedConnection,
                                 Q_ARG(dict, payload))

    def _emit_game_started(self, payload):
        QMetaObject.invokeMethod(self, "game_started", Qt.QueuedConnection,
                                 Q_ARG(dict, payload))

    def _emit_game_state(self, state):
        display = self._client.get_display_state()
        if display:
            QMetaObject.invokeMethod(self, "game_state_changed", Qt.QueuedConnection,
                                     Q_ARG(object, display))

    def _emit_move(self, move):
        QMetaObject.invokeMethod(self, "move_received", Qt.QueuedConnection,
                                 Q_ARG(dict, move))

    def _emit_game_over(self, winner, result, sgf=None):
        QMetaObject.invokeMethod(self, "game_over", Qt.QueuedConnection,
                                 Q_ARG(str, winner), Q_ARG(str, result), Q_ARG(str, sgf or ""))

    def _emit_player_joined(self, players):
        QMetaObject.invokeMethod(self, "player_joined", Qt.QueuedConnection,
                                 Q_ARG(list, players))

    def _emit_player_left(self, name):
        QMetaObject.invokeMethod(self, "player_left", Qt.QueuedConnection,
                                 Q_ARG(str, name))

    def _emit_chat(self, sender, text):
        QMetaObject.invokeMethod(self, "chat_message", Qt.QueuedConnection,
                                 Q_ARG(str, sender), Q_ARG(str, text))

    def _emit_undo_request(self, requester):
        QMetaObject.invokeMethod(self, "undo_requested", Qt.QueuedConnection,
                                 Q_ARG(str, requester))

    def _emit_undo_response(self, accepted):
        QMetaObject.invokeMethod(self, "undo_responded", Qt.QueuedConnection,
                                 Q_ARG(bool, accepted))

    # --- Публичные методы (вызываются из GUI-потока) ---
    def connect_to_server(self):
        self._thread.submit(self._client.connect())

    def disconnect_from_server(self):
        self._thread.submit(self._client.disconnect())

    def refresh_rooms(self):
        """Повторно запросить список комнат."""
        self._thread.submit(self._client._send(Message.lobby_ready()))

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

    def respond_undo(self, accepted: bool):
        """Ответить на запрос отмены хода."""
        self._thread.submit(self._client._send(Message.undo_response(accepted)))

    def send_chat(self, text):
        self._thread.submit(self._client.send_chat(text))

    def get_display_state(self):
        return self._client.get_display_state()

    def get_sgf(self):
        return self._client.get_sgf()

    def save_game(self, filepath=None):
        return self._client.save_game(filepath)

    def shutdown(self):
        self.disconnect_from_server()
        self._thread.stop()

    @property
    def player_name(self):
        return self._client.player_name

    @property
    def room_id(self):
        return self._client.room_id

    @property
    def player_color(self):
        return self._client.player_color


# ============================================================================
# 3. Виджет игровой доски (QPainter)
# ============================================================================

class GoBoardWidget(QFrame):
    stone_clicked = Signal(int, int)   # x, y (0-based)

    def __init__(self, board_size: int = 19, parent=None):
        super().__init__(parent)
        self.board_size = board_size
        self.board_array: List[List[int]] = []
        self.last_move: Optional[Dict] = None
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)

    def set_board(self, array: List[List[int]], last_move: Optional[Dict] = None):
        self.board_array = array
        self.last_move = last_move
        self.update()

    def _cell_size(self) -> float:
        w = self.width()
        h = self.height()
        margin = 20
        available = min(w, h) - 2 * margin
        return available / (self.board_size - 1) if self.board_size > 1 else available

    def _margin(self) -> float:
        return 20

    def _to_board_coords(self, px: int, py: int) -> Optional[tuple]:
        margin = self._margin()
        cell = self._cell_size()
        if cell <= 0:
            return None
        x = round((px - margin) / cell)
        y = round((py - margin) / cell)
        if 0 <= x < self.board_size and 0 <= y < self.board_size:
            return x, y
        return None

    def mousePressEvent(self, event: QMouseEvent):
        coords = self._to_board_coords(event.pos().x(), event.pos().y())
        if coords is not None:
            self.stone_clicked.emit(coords[0], coords[1])
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        margin = self._margin()
        cell = self._cell_size()
        if cell <= 0:
            return

        # Фон доски
        painter.fillRect(self.rect(), QColor("#dcb35c"))

        # Линии сетки
        pen = QPen(QColor("#000000"))
        pen.setWidth(1)
        painter.setPen(pen)
        size = self.board_size
        end = margin + cell * (size - 1)
        for i in range(size):
            pos = margin + cell * i
            painter.drawLine(int(margin), int(pos), int(end), int(pos))
            painter.drawLine(int(pos), int(margin), int(pos), int(end))

        # Хоши
        hoshi_points = []
        if size == 19:
            hoshi_points = [(3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15)]
        elif size == 13:
            hoshi_points = [(3,3),(3,9),(9,3),(9,9),(6,6)]
        elif size == 9:
            hoshi_points = [(2,2),(2,6),(6,2),(6,6),(4,4)]
        painter.setBrush(QBrush(QColor("#000000")))
        for hx, hy in hoshi_points:
            cx = margin + cell * hx
            cy = margin + cell * hy
            r = max(2, cell * 0.12)
            painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))

        # Камни
        for y in range(size):
            for x in range(size):
                if y >= len(self.board_array) or x >= len(self.board_array[y]):
                    continue
                val = self.board_array[y][x]
                if val == 0:
                    continue
                cx = margin + cell * x
                cy = margin + cell * y
                r = max(4, cell * 0.45)
                if val == 1:
                    painter.setBrush(QBrush(QColor("#000000")))
                    painter.setPen(QPen(QColor("#333333")))
                else:
                    painter.setBrush(QBrush(QColor("#ffffff")))
                    painter.setPen(QPen(QColor("#cccccc")))
                painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))

        # Последний ход — красный кружок
        if self.last_move and not self.last_move.get("is_pass"):
            lx = self.last_move.get("x", -1)
            ly = self.last_move.get("y", -1)
            if 0 <= lx < size and 0 <= ly < size:
                cx = margin + cell * lx
                cy = margin + cell * ly
                r = max(3, cell * 0.2)
                painter.setBrush(Qt.NoBrush)
                pen = QPen(QColor("#ff0000"))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawEllipse(QPoint(int(cx), int(cy)), int(r), int(r))

        painter.end()


# ============================================================================
# 4. Главное окно (стек экранов)
# ============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS-GO Network")
        self.resize(900, 700)
        self.client: Optional[QtNetworkClient] = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._build_connect_page()
        self._build_lobby_page()
        self._build_room_page()
        self._build_game_page()

        self.stack.setCurrentIndex(0)

    def _build_connect_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        form = QFormLayout()
        self.edit_name = QLineEdit("Player")
        self.edit_server = QLineEdit("ws://localhost:8765")
        self.edit_server.setMinimumWidth(300)
        form.addRow("Имя:", self.edit_name)
        form.addRow("Сервер:", self.edit_server)

        self.btn_connect = QPushButton("Подключиться")
        self.btn_connect.setMinimumHeight(40)
        self.btn_connect.clicked.connect(self.on_connect)

        self.lbl_connect_status = QLabel("")
        self.lbl_connect_status.setStyleSheet("color: red;")

        layout.addStretch()
        layout.addLayout(form)
        layout.addWidget(self.btn_connect)
        layout.addWidget(self.lbl_connect_status)
        layout.addStretch()

        self.stack.addWidget(page)

    def _build_lobby_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        top = QHBoxLayout()
        self.lbl_lobby_title = QLabel("Лобби")
        top.addWidget(self.lbl_lobby_title)
        top.addStretch()
        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self.on_refresh_rooms)
        top.addWidget(self.btn_refresh)
        self.btn_create_room = QPushButton("➕ Создать комнату")
        self.btn_create_room.clicked.connect(self.on_create_room_dialog)
        top.addWidget(self.btn_create_room)
        layout.addLayout(top)

        self.table_rooms = QTableWidget()
        self.table_rooms.setColumnCount(6)
        self.table_rooms.setHorizontalHeaderLabels(
            ["ID", "Название", "Хост", "Размер", "Игроки", "Пароль"]
        )
        self.table_rooms.horizontalHeader().setStretchLastSection(True)
        self.table_rooms.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_rooms.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_rooms.doubleClicked.connect(self.on_join_selected_room)
        layout.addWidget(self.table_rooms)

        bottom = QHBoxLayout()
        self.btn_join_room = QPushButton("Войти в комнату")
        self.btn_join_room.clicked.connect(self.on_join_selected_room)
        self.btn_disconnect = QPushButton("Отключиться")
        self.btn_disconnect.clicked.connect(self.on_disconnect)
        bottom.addWidget(self.btn_join_room)
        bottom.addStretch()
        bottom.addWidget(self.btn_disconnect)
        layout.addLayout(bottom)

        self.stack.addWidget(page)

    def _build_room_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.lbl_room_info = QLabel("Комната")
        layout.addWidget(self.lbl_room_info)

        self.list_players = QTextEdit()
        self.list_players.setReadOnly(True)
        self.list_players.setMaximumHeight(120)
        layout.addWidget(self.list_players)

        self.lbl_room_chat = QLabel("Чат комнаты:")
        layout.addWidget(self.lbl_room_chat)
        self.txt_room_chat = QTextEdit()
        self.txt_room_chat.setReadOnly(True)
        self.txt_room_chat.setMaximumHeight(150)
        layout.addWidget(self.txt_room_chat)

        chat_input = QHBoxLayout()
        self.edit_room_chat = QLineEdit()
        self.edit_room_chat.setPlaceholderText("Сообщение...")
        self.edit_room_chat.returnPressed.connect(self.on_send_room_chat)
        self.btn_send_room_chat = QPushButton("Отправить")
        self.btn_send_room_chat.clicked.connect(self.on_send_room_chat)
        chat_input.addWidget(self.edit_room_chat)
        chat_input.addWidget(self.btn_send_room_chat)
        layout.addLayout(chat_input)

        buttons = QHBoxLayout()
        self.btn_ready = QPushButton("✅ Готов")
        self.btn_ready.clicked.connect(lambda: self.client.set_ready(True))
        self.btn_unready = QPushButton("⏳ Не готов")
        self.btn_unready.clicked.connect(lambda: self.client.set_ready(False))
        self.btn_leave_room = QPushButton("🚪 Покинуть комнату")
        self.btn_leave_room.clicked.connect(self.on_leave_room)
        buttons.addWidget(self.btn_ready)
        buttons.addWidget(self.btn_unready)
        buttons.addStretch()
        buttons.addWidget(self.btn_leave_room)
        layout.addLayout(buttons)

        self.stack.addWidget(page)

    def _build_game_page(self):
        page = QWidget()
        main = QHBoxLayout(page)

        left = QVBoxLayout()
        self.lbl_game_status = QLabel("Игра")
        left.addWidget(self.lbl_game_status)

        self.board = GoBoardWidget(19)
        self.board.stone_clicked.connect(self.on_board_click)
        left.addWidget(self.board, stretch=1)

        game_buttons = QHBoxLayout()
        self.btn_pass = QPushButton("Пас")
        self.btn_pass.clicked.connect(self.on_pass)
        self.btn_resign = QPushButton("Сдаться")
        self.btn_resign.clicked.connect(self.on_resign)
        self.btn_undo = QPushButton("Отменить ход")
        self.btn_undo.clicked.connect(self.on_request_undo)
        self.btn_save_sgf = QPushButton("💾 SGF")
        self.btn_save_sgf.clicked.connect(self.on_save_sgf)
        game_buttons.addWidget(self.btn_pass)
        game_buttons.addWidget(self.btn_resign)
        game_buttons.addWidget(self.btn_undo)
        game_buttons.addWidget(self.btn_save_sgf)
        game_buttons.addStretch()
        left.addLayout(game_buttons)

        main.addLayout(left, stretch=2)

        right = QVBoxLayout()
        self.lbl_game_info = QLabel("Информация")
        right.addWidget(self.lbl_game_info)

        self.txt_game_chat = QTextEdit()
        self.txt_game_chat.setReadOnly(True)
        right.addWidget(self.txt_game_chat, stretch=1)

        chat_row = QHBoxLayout()
        self.edit_game_chat = QLineEdit()
        self.edit_game_chat.setPlaceholderText("Чат...")
        self.edit_game_chat.returnPressed.connect(self.on_send_game_chat)
        self.btn_send_game_chat = QPushButton("▶")
        self.btn_send_game_chat.clicked.connect(self.on_send_game_chat)
        chat_row.addWidget(self.edit_game_chat)
        chat_row.addWidget(self.btn_send_game_chat)
        right.addLayout(chat_row)

        self.btn_back_to_lobby = QPushButton("🏠 Вернуться в лобби")
        self.btn_back_to_lobby.clicked.connect(self.on_back_to_lobby)
        right.addWidget(self.btn_back_to_lobby)

        main.addLayout(right, stretch=1)
        self.stack.addWidget(page)

    # === Слоты ===

    def on_connect(self):
        name = self.edit_name.text().strip()
        server = self.edit_server.text().strip()
        if not name or not server:
            QMessageBox.warning(self, "Ошибка", "Введите имя и адрес сервера")
            return
        self.lbl_connect_status.setText("Подключение...")
        self.client = QtNetworkClient(server, name, self)
        self.client.connected.connect(self.on_connected)
        self.client.disconnected.connect(self.on_disconnected)
        self.client.error_occurred.connect(self.on_error)
        self.client.room_list_received.connect(self.on_room_list)
        self.client.room_joined.connect(self.on_room_joined)
        self.client.room_updated.connect(self.on_room_updated)
        self.client.game_started.connect(self.on_game_started)
        self.client.game_state_changed.connect(self.on_game_state_changed)
        self.client.move_received.connect(self.on_move_received)
        self.client.game_over.connect(self.on_game_over)
        self.client.player_joined.connect(self.on_player_joined)
        self.client.player_left.connect(self.on_player_left)
        self.client.chat_message.connect(self.on_chat_message)
        self.client.undo_requested.connect(self.on_undo_requested)
        self.client.undo_responded.connect(self.on_undo_responded)
        self.client.connect_to_server()

    def on_connected(self):
        self.lbl_connect_status.setText("")
        self.lbl_lobby_title.setText(f"Лобби — {self.client.player_name}")
        self.stack.setCurrentIndex(1)

    def on_disconnected(self):
        QMessageBox.information(self, "Отключение", "Соединение с сервером разорвано")
        self.stack.setCurrentIndex(0)
        if self.client:
            self.client.shutdown()
            self.client = None

    def on_error(self, code: str, message: str):
        QMessageBox.critical(self, f"Ошибка [{code}]", message)

    def on_refresh_rooms(self):
        if self.client:
            self.client.refresh_rooms()

    def on_room_list(self, rooms: List[RoomInfo]):
        self.table_rooms.setRowCount(len(rooms))
        for i, room in enumerate(rooms):
            self.table_rooms.setItem(i, 0, QTableWidgetItem(str(room.room_id)))
            self.table_rooms.setItem(i, 1, QTableWidgetItem(str(room.name)))
            self.table_rooms.setItem(i, 2, QTableWidgetItem(str(room.host_name)))
            self.table_rooms.setItem(i, 3, QTableWidgetItem(f"{room.board_size}x{room.board_size}"))
            self.table_rooms.setItem(i, 4, QTableWidgetItem(f"{room.player_count}/{room.max_players}"))
            lock = "🔒" if room.has_password else ""
            self.table_rooms.setItem(i, 5, QTableWidgetItem(lock))

    def on_create_room_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Создать комнату")
        layout = QFormLayout(dlg)

        edit_name = QLineEdit(f"Room_{self.client.player_name}")
        spin_size = QSpinBox()
        spin_size.setRange(9, 19)
        spin_size.setSingleStep(2)
        spin_size.setValue(19)
        spin_size.setWrapping(False)
        edit_pass = QLineEdit()
        edit_pass.setPlaceholderText("(без пароля)")
        spin_komi = QDoubleSpinBox()
        spin_komi.setRange(0.5, 20.0)
        spin_komi.setValue(6.5)
        spin_komi.setDecimals(1)
        combo_rules = QComboBox()
        combo_rules.addItems(["japanese", "chinese", "korean"])

        layout.addRow("Название:", edit_name)
        layout.addRow("Размер:", spin_size)
        layout.addRow("Пароль:", edit_pass)
        layout.addRow("Коми:", spin_komi)
        layout.addRow("Правила:", combo_rules)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() == QDialog.Accepted:
            pwd = edit_pass.text().strip() or None
            self.client.create_room(
                edit_name.text(), spin_size.value(), pwd,
                spin_komi.value(), combo_rules.currentText()
            )

    def on_join_selected_room(self):
        row = self.table_rooms.currentRow()
        if row < 0:
            QMessageBox.information(self, "Внимание", "Выберите комнату")
            return
        room_id = self.table_rooms.item(row, 0).text()
        has_pwd = self.table_rooms.item(row, 5).text() == "🔒"
        pwd = None
        if has_pwd:
            pwd, ok = QInputDialog.getText(self, "Пароль", "Введите пароль:", QLineEdit.Password)
            if not ok:
                return
            pwd = pwd.strip() or None
        self.client.join_room(room_id, pwd)

    def on_room_joined(self, room_id: str, color: str):
        self.lbl_room_info.setText(f"Комната: {room_id} | Вы играете: {color}")
        self.stack.setCurrentIndex(2)

    def on_room_updated(self, payload: dict):
        players = payload.get("players", [])
        text = ""
        for p in players:
            ready = "✅" if p.get("is_ready") else "⏳"
            text += f"{ready} {p.get('name', '?')} ({p.get('color', '?')})\n"
        self.list_players.setPlainText(text)

    def on_player_joined(self, players: list):
        self.on_room_updated({"players": players})

    def on_player_left(self, name: str):
        self.txt_room_chat.append(f"<i>{name} покинул комнату</i>")

    def on_chat_message(self, sender: str, text: str):
        if self.stack.currentIndex() == 2:
            self.txt_room_chat.append(f"&lt;{sender}&gt; {text}")
        elif self.stack.currentIndex() == 3:
            self.txt_game_chat.append(f"&lt;{sender}&gt; {text}")

    def on_send_room_chat(self):
        text = self.edit_room_chat.text().strip()
        if text and self.client:
            self.client.send_chat(text)
            self.edit_room_chat.clear()

    def on_send_game_chat(self):
        text = self.edit_game_chat.text().strip()
        if text and self.client:
            self.client.send_chat(text)
            self.edit_game_chat.clear()

    def on_leave_room(self):
        if self.client:
            self.client.leave_room()
        self.stack.setCurrentIndex(1)

    def on_game_started(self, payload: dict):
        size = payload.get("board_size", 19)
        self.board.board_size = size
        self.board.set_board([[0]*size for _ in range(size)])
        self.lbl_game_status.setText(
            f"Игра началась! Размер: {size}x{size} | Вы: {self.client.player_color}"
        )
        self.txt_game_chat.clear()
        self.stack.setCurrentIndex(3)

    def on_game_state_changed(self, state: GameDisplayState):
        self.board.set_board(state.board_array, state.last_move)
        turn = "○ Черные" if state.current_player == "black" else "● Белые"
        my = "ВАШ ХОД!" if state.is_my_turn else "Ход противника"
        self.lbl_game_status.setText(
            f"Ход {state.move_number} | {turn} | {my} | "
            f"Захваты: ⚫{state.captures.get('black',0)} ⚪{state.captures.get('white',0)}"
        )

    def on_move_received(self, move: dict):
        pass

    def on_board_click(self, x: int, y: int):
        if self.client:
            self.client.send_move(x, y)

    def on_pass(self):
        if self.client:
            self.client.send_pass()

    def on_resign(self):
        reply = QMessageBox.question(self, "Сдаться", "Вы уверены?")
        if reply == QMessageBox.Yes and self.client:
            self.client.send_resign()

    def on_request_undo(self):
        if self.client:
            self.client.request_undo()

    def on_undo_requested(self, requester: str):
        reply = QMessageBox.question(
            self, "Отмена хода",
            f"{requester} просит отменить ход. Согласны?"
        )
        if self.client:
            accepted = (reply == QMessageBox.Yes)
            self.client.respond_undo(accepted)

    def on_undo_responded(self, accepted: bool):
        if accepted:
            QMessageBox.information(self, "Отмена", "Ход отменён")
        else:
            QMessageBox.information(self, "Отмена", "Оппонент отказал")

    def on_game_over(self, winner: str, result: str, sgf: str):
        QMessageBox.information(
            self, "Игра окончена",
            f"Победитель: {winner}\nРезультат: {result}"
        )
        self.txt_game_chat.append(f"<b>Игра окончена:</b> {winner} — {result}")

    def on_save_sgf(self):
        if not self.client:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить SGF", "game.sgf", "SGF (*.sgf)")
        if path:
            saved = self.client.save_game(path)
            if saved:
                QMessageBox.information(self, "Сохранено", f"Файл: {saved}")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить")

    def on_back_to_lobby(self):
        self.stack.setCurrentIndex(1)
        self.on_refresh_rooms()

    def on_disconnect(self):
        if self.client:
            self.client.disconnect_from_server()
        self.stack.setCurrentIndex(0)

    def closeEvent(self, event):
        if self.client:
            self.client.shutdown()
        event.accept()


# ============================================================================
# 5. Точка входа
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()