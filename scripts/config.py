# config.py (дополненная версия)

import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
GAMES_DIR = BASE_DIR / "games"

#создаем поддиректории
for subdir in ['pvp', 'pve', 'puzzles', 'reviews', 'autosave', 'loaded']:
    (GAMES_DIR / subdir).mkdir(parents=True, exist_ok=True)

def get_sgf_path(game_mode: str = "autosave", filename: str = None) -> str:
    """Генерация пути для сохранения SGF"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"go_{game_mode}_{timestamp}.sgf"
    else:
        #добавляем .sgf если не указано
        if not filename.endswith('.sgf'):
            filename = f"{filename}.sgf"
    
    return str(GAMES_DIR / game_mode / filename)

def get_saves_dir(game_mode: str = None):
    """
    Возвращает путь к директории с сохранениями.
    
    Параметры:
        game_mode: str - 'pvp', 'pve', 'loaded', 'autosave' и т.д.
                   Если None, возвращает корневую папку games
    """
    if game_mode is None:
        return str(GAMES_DIR)
    return str(GAMES_DIR / game_mode)
