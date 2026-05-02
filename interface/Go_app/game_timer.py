from PySide6.QtCore import QTimer, QObject, Signal

class GameTimer(QObject):
    time_changed = Signal(int, int)  # player, time_remaining
    time_expired = Signal(int)  # player
    
    def __init__(self, player, initial_time, parent=None):
        super().__init__(parent)
        self.player = player
        self.time_remaining = initial_time
        self.timer = QTimer()
        self.timer.timeout.connect(self.decrement)
        self.is_running = False
        
    def start(self):
        self.is_running = True
        self.timer.start(1000)  # каждую секунду
        
    def stop(self):
        self.is_running = False
        self.timer.stop()
        
    def decrement(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.time_changed.emit(self.player, self.time_remaining)
            
            if self.time_remaining == 0:
                self.time_expired.emit(self.player)
                self.stop()
    
    def reset(self, new_time):
        """Сбросить таймер с новым временем"""
        self.stop()
        self.time_remaining = new_time
        self.time_changed.emit(self.player, self.time_remaining)