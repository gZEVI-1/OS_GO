from PySide6.QtCore import QTimer, QObject, Signal
import time

class GameTimer(QObject):
    time_changed = Signal()
    time_expired = Signal(int)
    
    def __init__(self, player_num, initial_time, parent=None, no_time_limit=False):
        super().__init__(parent)
        self.player_num = player_num
        self.initial_time = initial_time  
        self._time_remaining_ms = initial_time * 1000  # в миллисекундах
        self.no_time_limit = no_time_limit
        self.is_running = False
        self._start_time_ms = None  
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._tick)
        self.update_timer.setInterval(50)  #каждые 50 мс для большей точности
    
    @property
    def time_remaining(self):
        return self.time_remaining_ms / 1000.0
    
    @property
    def time_remaining_ms(self):
        if not self.is_running or self._start_time_ms is None:
            return self._time_remaining_ms
        
        elapsed_ms = int((time.time() * 1000) - self._start_time_ms)
        return max(0, self._time_remaining_ms - elapsed_ms)
    
    def start(self):
        if self.no_time_limit:
            return
        if self.is_running:
            return
        
        self.is_running = True
        self._start_time_ms = time.time() * 1000
        self.update_timer.start()
        self.time_changed.emit()
    
    def stop(self):
        if not self.is_running:
            return
        
        if self._start_time_ms is not None:
            elapsed_ms = int((time.time() * 1000) - self._start_time_ms)
            self._time_remaining_ms = max(0, self._time_remaining_ms - elapsed_ms)
        
        self.is_running = False
        self.update_timer.stop()
        self._start_time_ms = None
        self.time_changed.emit()
    
    def _tick(self):
        if not self.is_running or self.no_time_limit:
            return
        
        current_time_ms = self.time_remaining_ms
        
        if current_time_ms <= 0:
            self._time_remaining_ms = 0
            self.stop()
            self.time_expired.emit(self.player_num)
        else:
            self.time_changed.emit()
    
    def reset(self):
        self.stop()
        self._time_remaining_ms = self.initial_time * 1000
        self.time_changed.emit()