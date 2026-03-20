import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
#print(f"📁 Базовая директория: {BASE_DIR}")
GAMES_DIR = BASE_DIR / "games"
SAVES_DIR = BASE_DIR / "saves"


for subdir in ['pvp', 'pve', 'puzzles', 'reviews', 'autosave']:
    (GAMES_DIR / subdir).mkdir(parents=True, exist_ok=True)

def get_sgf_path(game_mode: str="autosave", filename: str = None) -> Path:
    """Генерация пути для сохранения SGF"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"go_{game_mode}_{timestamp}.sgf"
    else:
        filename = f"{filename}.sgf"
    
    return str(GAMES_DIR / game_mode / filename)