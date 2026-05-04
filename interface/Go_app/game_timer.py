# game_timer.py
from PySide6.QtCore import QTimer, QObject, Signal
import time

class GameTimer(QObject):
    time_changed = Signal()
    time_expired = Signal(int)
    
    def __init__(self, player_num, initial_time, parent=None, no_time_limit=False):
        super().__init__(parent)
        self.player_num = player_num
        self.initial_time = initial_time
        self._time_remaining = initial_time  
        self.no_time_limit = no_time_limit
        self.is_running = False
        self._start_time = None
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._tick)
        self.update_timer.setInterval(100)  
    
    @property
    def time_remaining(self):
        if not self.is_running or self._start_time is None:
            return self._time_remaining
        
        elapsed = time.time() - self._start_time
        return max(0, self._time_remaining - elapsed)
    
    def start(self):
        if self.no_time_limit:
            return
        if self.is_running:
            return
        
        self.is_running = True
        self._start_time = time.time()
        self.update_timer.start()
        self.time_changed.emit()
    
    def stop(self):
        if not self.is_running:
            return
        
        if self._start_time is not None:
            elapsed = time.time() - self._start_time
            self._time_remaining = max(0, self._time_remaining - elapsed)
        
        self.is_running = False
        self.update_timer.stop()
        self._start_time = None
        self.time_changed.emit()
    
    def _tick(self):
        if not self.is_running or self.no_time_limit:
            return
        
        current_time = self.time_remaining
        
        if current_time <= 0:
            # Время истекло
            self._time_remaining = 0
            self.stop()
            self.time_expired.emit(self.player_num)
        else:
            self.time_changed.emit()
    
    def reset(self):
        self.stop()
        self._time_remaining = self.initial_time
        self.time_changed.emit()