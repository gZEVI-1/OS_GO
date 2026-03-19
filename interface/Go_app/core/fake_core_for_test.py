class MockCoreAPI:
    def __init__(self, size=19):
        self.board_size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        self.current_player = 1
        self.game_over = False
        self.winner = 0

    def get_board(self):
        return self.board

    def get_current_player(self):
        return self.current_player

    def make_move(self, row, col):
        if self.board[row][col] == 0:
            self.board[row][col] = self.current_player
            self.current_player = 3 - self.current_player
            return {'success': True}
        return {'success': False}

    def is_game_over(self):
        return self.game_over

    def get_winner(self):
        return self.winner
