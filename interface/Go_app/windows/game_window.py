from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from generated.ui_game_window import Ui_main 
from windows.base_window import BaseWindow
from windows.profile_window import ProfileWindow

class GameWindow(BaseWindow):
    def __init__(self, navigation, board_size=19, core_api=None):
        super().__init__(navigation)
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.board_size = board_size
        
        #CORE_API_HERE 
        self.core_api = core_api
        
        self.board_widget = self.ui.boardWidget
        self.board_widget.set_board_size(board_size)
        if self.core_api:
            self.board_widget.set_core_api(self.core_api)
        self.board_widget.cell_clicked.connect(self.on_cell_clicked)
        self.board_widget.move_made.connect(self.on_move_made)
        self.board_widget.game_over.connect(self.on_game_over)
        self.board_widget.invalid_move.connect(self.on_invalid_move)

        self.player_data = {
            'name': 'Игрок', 'rating': 1600, 'wins': 42, 'losses': 17,
            'country': 'Россия', 'avatar_path': None
        }
        self.opponent_data = {
            'name': 'Противник', 'rating': 1850, 'wins': 127, 'losses': 83,
            'country': 'США', 'avatar_path': None
        }
        self.ui.playerName.setText(self.player_data['name'])
        self.ui.opponentName.setText(self.opponent_data['name'])
        self.ui.playerAvatar.clicked.connect(self.show_player_profile)
        self.ui.opponentAvatar.clicked.connect(self.show_opponent_profile)
        self.ui.buttonPass.clicked.connect(self.pass_move)
        self.ui.buttonResign.clicked.connect(self.resign)
        self.ui.timer.setText("⚫ 15:00")
        self.ui.buttonPrevMove.clicked.connect(self.prev_move)
        self.ui.buttonNextMove.clicked.connect(self.next_move)
        self.move_history = []
        self.setWindowTitle(f"Игра Го {board_size}×{board_size}")

    def show_player_profile(self):
        profile = ProfileWindow(self.player_data, self)
        profile.exec_()

    def show_opponent_profile(self):
        profile = ProfileWindow(self.opponent_data, self)
        profile.exec_()

    def on_cell_clicked(self, row, col):
        self.board_widget.request_move(row, col)

    def on_move_made(self, row, col, player):
        player_name = "Черные" if player == 1 else "Белые"
        print(f"✅ Ход {player_name}: ({row}, {col})")
        move_number = self.ui.historyList.count() + 1
        col_letter = chr(65 + col)
        move_text = f"{move_number}. {col_letter}{row + 1}"
        self.ui.historyList.addItem(move_text)
        #CORE_PLAYER_CHECK 
        if self.core_api:
            current = self.core_api.get_current_player()

    def on_game_over(self, winner):
        winner_text = {1: "Черные", 2: "Белые", 0: "Ничья"}.get(winner, "Неизвестно")
        QMessageBox.information(self, "Игра окончена", f"Победили: {winner_text}!")

    def on_invalid_move(self, row, col):
        print(f"❌ Недопустимый ход в ({row}, {col})")

    def pass_move(self):
        QMessageBox.information(self, "Пас", "Вы передали ход")

    def resign(self):
        reply = QMessageBox.question(self, "Сдаться",
                                   "Вы уверены, что хотите сдаться?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "Игра окончена", "Вы сдались. Победил противник!")

    def new_game(self):
        print("Новая игра")
        self.ui.historyList.clear()
        if hasattr(self.board_widget, 'clear_board'):
            self.board_widget.clear_board()

    def back_to_menu(self):
        self.navigation.close_current_and_open("main")

    def prev_move(self):
        current = self.ui.historyList.currentRow()
        if current > 0:
            self.ui.historyList.setCurrentRow(current - 1)

    def next_move(self):
        current = self.ui.historyList.currentRow()
        if current < self.ui.historyList.count() - 1:
            self.ui.historyList.setCurrentRow(current + 1)
