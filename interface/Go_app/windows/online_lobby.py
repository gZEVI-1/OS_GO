import sys
from pathlib import Path

_current_dir = Path(__file__).resolve().parent          # .../Go_app/windows
_go_app_dir = _current_dir.parent                      # .../Go_app
_project_root = _go_app_dir.parent.parent              # .../OS_GO
_network_pvp_path = _project_root / "scripts" / "network_pvp"

for p in (_network_pvp_path, _go_app_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout, QGroupBox,
    QRadioButton, QSpinBox, QCheckBox, QDialogButtonBox, QMessageBox,
    QHeaderView, QWidget, QInputDialog, QLabel, QTextEdit
)
from PySide6.QtCore import Qt, Signal

from windows.app_settings import AppSettings
from windows.network_client_wrapper import QtNetworkClient
from protocol import RoomInfo


class OnlineCreateRoomDialog(QDialog):
    """Диалог настроек для создания онлайн-комнаты (без komi и правил)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = AppSettings()
        self.setWindowTitle(self.settings.get_text("create_room_title"))
        self.setModal(True)
        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        group = QGroupBox()
        form = QFormLayout(group)

        # Размер доски
        self.radio9x9 = QRadioButton(self.settings.get_text("board_9x9"))
        self.radio13x13 = QRadioButton(self.settings.get_text("board_13x13"))
        self.radio19x19 = QRadioButton(self.settings.get_text("board_19x19"))
        self.radio19x19.setChecked(True)
        size_layout = QHBoxLayout()
        size_layout.addWidget(self.radio9x9)
        size_layout.addWidget(self.radio13x13)
        size_layout.addWidget(self.radio19x19)
        form.addRow(self.settings.get_text("board_size_label"), size_layout)

        # Время
        self.spinMainTime = QSpinBox()
        self.spinMainTime.setRange(1, 60)
        self.spinMainTime.setSuffix(" " + self.settings.get_text("minutes") if self.settings.get_text("minutes") else " мин")
        self.spinMainTime.setValue(10)
        self.spinByoyomi = QSpinBox()
        self.spinByoyomi.setRange(0, 60)
        self.spinByoyomi.setSuffix(" " + self.settings.get_text("seconds") if self.settings.get_text("seconds") else " сек")
        self.spinByoyomi.setValue(30)
        self.checkNoTimeLimit = QCheckBox(self.settings.get_text("no_time_limit"))
        self.checkNoTimeLimit.toggled.connect(self._toggle_time)

        form.addRow(self.settings.get_text("main_time_label"), self.spinMainTime)
        form.addRow(self.settings.get_text("byoyomi_label"), self.spinByoyomi)
        form.addRow("", self.checkNoTimeLimit)

        # Показывать разрешённые ходы
        self.checkLegalMoves = QCheckBox(self.settings.get_text("show_legal_moves"))
        self.checkLegalMoves.setChecked(True)
        form.addRow("", self.checkLegalMoves)

        # Пароль комнаты
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setPlaceholderText(self.settings.get_text("password_placeholder"))
        form.addRow(self.settings.get_text("room_password_label"), self.passwordEdit)

        layout.addWidget(group)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _toggle_time(self, checked):
        self.spinMainTime.setEnabled(not checked)
        self.spinByoyomi.setEnabled(not checked)

    def get_board_size(self) -> int:
        if self.radio9x9.isChecked():
            return 9
        if self.radio13x13.isChecked():
            return 13
        return 19

    def get_time_settings(self) -> dict:
        if self.checkNoTimeLimit.isChecked():
            return {"no_time_limit": True, "main_time": None, "byoyomi": None}
        return {
            "no_time_limit": False,
            "main_time": self.spinMainTime.value() * 60,
            "byoyomi": self.spinByoyomi.value()
        }

    def get_visual_settings(self) -> dict:
        return {"show_legal_moves": self.checkLegalMoves.isChecked()}

    def get_room_password(self):
        pwd = self.passwordEdit.text().strip()
        return pwd if pwd else None

    def apply_theme(self):
        self.setStyleSheet(AppSettings().get_stylesheet())


class OnlineLobbyDialog(QDialog):
    """Главный диалог: Создать комнату / Присоединиться / Комната ожидания."""
    game_ready = Signal(dict)

    def __init__(self, player_name: str, parent=None):
        super().__init__(parent)
        self.player_name = player_name
        self.settings = AppSettings()
        self.client = None
        self.current_rooms = []
        self.pending_game_settings = {}
        self._joined_room_id = None
        self._joined_color = None

        self.setWindowTitle(self.settings.get_text("online_game_title"))
        self.resize(800, 600)
        self.setModal(True)
        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        # ---- Страница 0: Выбор действия ----
        page_choose = QWidget()
        choose_layout = QVBoxLayout(page_choose)
        choose_layout.setAlignment(Qt.AlignCenter)
        self.btn_create = QPushButton(self.settings.get_text("create_room_button"))
        self.btn_create.setMinimumHeight(60)
        self.btn_join = QPushButton(self.settings.get_text("join_room_button"))
        self.btn_join.setMinimumHeight(60)
        choose_layout.addWidget(self.btn_create)
        choose_layout.addWidget(self.btn_join)
        self.stacked.addWidget(page_choose)

        # ---- Страница 1: Список комнат ----
        page_join = QWidget()
        join_layout = QVBoxLayout(page_join)
        self.table_rooms = QTableWidget(0, 6)
        self.table_rooms.setHorizontalHeaderLabels(["ID", self.settings.get_text("room_name_header"),
                                                    self.settings.get_text("host_header"),
                                                    self.settings.get_text("size_header"),
                                                    self.settings.get_text("players_header"),
                                                    self.settings.get_text("password_header")])
        self.table_rooms.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_rooms.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_rooms.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_rooms.doubleClicked.connect(self._join_selected_room)
        join_layout.addWidget(self.table_rooms)

        btn_refresh = QPushButton(self.settings.get_text("refresh_button"))
        btn_refresh.clicked.connect(self.refresh_rooms)
        btn_join = QPushButton(self.settings.get_text("join_selected_button"))
        btn_join.clicked.connect(self._join_selected_room)
        btn_back = QPushButton(self.settings.get_text("back_button"))
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(btn_back)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_refresh)
        bottom_layout.addWidget(btn_join)
        join_layout.addLayout(bottom_layout)
        self.stacked.addWidget(page_join)

        # ---- Страница 2: Комната ожидания ----
        page_room = QWidget()
        room_layout = QVBoxLayout(page_room)

        self.lbl_room_title = QLabel(self.settings.get_text("room_label"))
        room_layout.addWidget(self.lbl_room_title)

        self.list_room_players = QTextEdit()
        self.list_room_players.setReadOnly(True)
        self.list_room_players.setMaximumHeight(120)
        room_layout.addWidget(self.list_room_players)

        self.txt_room_chat = QTextEdit()
        self.txt_room_chat.setReadOnly(True)
        self.txt_room_chat.setMaximumHeight(150)
        room_layout.addWidget(self.txt_room_chat)

        chat_input = QHBoxLayout()
        self.edit_room_chat = QLineEdit()
        self.edit_room_chat.setPlaceholderText(self.settings.get_text("chat_placeholder"))
        self.edit_room_chat.returnPressed.connect(self._send_room_chat)
        btn_send_chat = QPushButton(self.settings.get_text("send_button"))
        btn_send_chat.clicked.connect(self._send_room_chat)
        chat_input.addWidget(self.edit_room_chat)
        chat_input.addWidget(btn_send_chat)
        room_layout.addLayout(chat_input)

        self.btn_ready = QPushButton(f"✅ {self.settings.get_text('ready_button')}")
        self.btn_ready.clicked.connect(self._on_ready_clicked)
        btn_leave = QPushButton(f"🚪 {self.settings.get_text('leave_room_button')}")
        btn_leave.clicked.connect(self._on_leave_room)
        room_btns = QHBoxLayout()
        room_btns.addWidget(self.btn_ready)
        room_btns.addStretch()
        room_btns.addWidget(btn_leave)
        room_layout.addLayout(room_btns)
        self.stacked.addWidget(page_room)

        # Подключения
        self.btn_create.clicked.connect(self._on_create_clicked)
        self.btn_join.clicked.connect(self._on_join_clicked)
        btn_back.clicked.connect(lambda: self.stacked.setCurrentIndex(0))

    def apply_theme(self):
        self.setStyleSheet(self.settings.get_stylesheet())

    # ---------- Создание комнаты ----------
    def _on_create_clicked(self):
        dialog = OnlineCreateRoomDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        board_size = dialog.get_board_size()
        time_settings = dialog.get_time_settings()
        visual_settings = dialog.get_visual_settings()
        password = dialog.get_room_password()

        self.pending_game_settings = {
            "board_size": board_size,
            "time": time_settings,
            "visual": visual_settings,
            "password": password
        }

        if self.client is None:
            self._connect_to_server(callback=lambda: self._create_room(board_size, password))
        else:
            self._create_room(board_size, password)

    def _create_room(self, board_size, password):
        room_name = f"{self.settings.get_text('default_room_name')} {self.player_name}"
        self.client.create_room(
            name=room_name,
            board_size=board_size,
            password=password,
            komi=6.5,
            rules="japanese"
        )

    # ---------- Присоединение ----------
    def _on_join_clicked(self):
        if self.client is None:
            self._connect_to_server(callback=self._show_join_page)
        else:
            self._show_join_page()

    def _show_join_page(self):
        self.stacked.setCurrentIndex(1)
        self.refresh_rooms()

    def refresh_rooms(self):
        if self.client:
            self.client.refresh_rooms()

    def _join_selected_room(self):
        row = self.table_rooms.currentRow()
        if row < 0:
            QMessageBox.information(self, self.settings.get_text("attention"),
                                    self.settings.get_text("select_room_warning"))
            return
        room = self.current_rooms[row]
        password = None
        if room.has_password:
            pwd, ok = QInputDialog.getText(self, self.settings.get_text("password_dialog_title"),
                                           self.settings.get_text("password_dialog_label"),
                                           QLineEdit.Password)
            if not ok:
                return
            password = pwd.strip() or None

        # Сохраняем настройки комнаты для GameWindowOnline
        self.pending_game_settings["board_size"] = room.board_size
        self.client.join_room(room.room_id, password)

    # ---------- Комната ожидания ----------
    def _on_ready_clicked(self):
        if self.client:
            self.client.set_ready(True)
            self.btn_ready.setEnabled(False)
            self.btn_ready.setText(f"⏳ {self.settings.get_text('waiting_opponent')}")

    def _on_leave_room(self):
        if self.client:
            self.client.leave_room()
        self.btn_ready.setEnabled(True)
        self.btn_ready.setText(f"✅ {self.settings.get_text('ready_button')}")
        self.stacked.setCurrentIndex(0)

    def _send_room_chat(self):
        text = self.edit_room_chat.text().strip()
        if text and self.client:
            self.client.send_chat(text)
            self.edit_room_chat.clear()

    # ---------- Подключение к серверу ----------
    def _connect_to_server(self, callback=None):
        server_url = "ws://localhost:8765"
        self.client = QtNetworkClient(server_url, self.player_name, self)
        self.client.connected.connect(lambda: self._on_client_connected(callback))
        self.client.room_list_received.connect(self._on_room_list)
        self.client.room_joined.connect(self._on_room_joined)
        self.client.room_updated.connect(self._on_room_updated)
        self.client.game_started.connect(self._on_game_started)
        self.client.chat_message.connect(self._on_chat_message)
        self.client.error_occurred.connect(self._on_error)
        self.client.disconnected.connect(self._on_disconnected)
        self.client.connect_to_server()

    def _on_client_connected(self, callback):
        if callback:
            callback()

    def _on_room_list(self, rooms):
        self.current_rooms = rooms
        self.table_rooms.setRowCount(len(rooms))
        for i, room in enumerate(rooms):
            self.table_rooms.setItem(i, 0, QTableWidgetItem(room.room_id))
            self.table_rooms.setItem(i, 1, QTableWidgetItem(room.name))
            self.table_rooms.setItem(i, 2, QTableWidgetItem(room.host_name))
            self.table_rooms.setItem(i, 3, QTableWidgetItem(f"{room.board_size}x{room.board_size}"))
            self.table_rooms.setItem(i, 4, QTableWidgetItem(f"{room.player_count}/{room.max_players}"))
            pwd_mark = "🔒" if room.has_password else ""
            self.table_rooms.setItem(i, 5, QTableWidgetItem(pwd_mark))

    def _on_room_joined(self, room_id: str, color: str):
        self._joined_room_id = room_id
        self._joined_color = color
        color_text = self.settings.get_text("black_color") if color == "black" else self.settings.get_text("white_color")
        self.lbl_room_title.setText(f"{self.settings.get_text('room_label')} {room_id} | "
                                    f"{self.settings.get_text('you_play')} {color_text}")
        self.stacked.setCurrentIndex(2)   # Переходим в комнату ожидания
        self.btn_ready.setEnabled(True)
        self.btn_ready.setText(f"✅ {self.settings.get_text('ready_button')}")
        self.txt_room_chat.clear()
        self.list_room_players.clear()

    def _on_room_updated(self, payload: dict):
        players = payload.get("players", [])
        text = ""
        for p in players:
            ready = "✅" if p.get("is_ready") else "⏳"
            text += f"{ready} {p.get('name', '?')} ({p.get('color', '?')})\n"
        self.list_room_players.setPlainText(text)

    def _on_chat_message(self, sender: str, text: str):
        self.txt_room_chat.append(f"<{sender}> {text}")

    def _on_game_started(self, payload: dict):
        game_data = {
            "client": self.client,
            "player_name": self.player_name,
            "player_color": self._joined_color,
            "room_id": self._joined_room_id,
            "board_size": payload.get("board_size", self.pending_game_settings.get("board_size", 19)),
            "time_settings": self.pending_game_settings.get("time", {}),
            "visual_settings": self.pending_game_settings.get("visual", {})
        }
        self.accept()
        self.game_ready.emit(game_data)

    def _on_error(self, code, msg):
        QMessageBox.critical(self, f"{self.settings.get_text('error_prefix')} {code}", msg)

    def _on_disconnected(self):
        QMessageBox.warning(self, self.settings.get_text("connection"), self.settings.get_text("connection_lost"))
        self.reject()