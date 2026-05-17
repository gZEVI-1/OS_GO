import json
import os
from PySide6.QtCore import QObject, Signal
from enum import Enum

class Language(Enum):
    RUSSIAN = "ru"
    ENGLISH = "en"

class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"
    ASIA = "asia"

class AppSettings(QObject):
    # Глобальные настройки приложения
    settings_changed = Signal()
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance    
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            self._language = Language.ENGLISH
            self._theme = Theme.ASIA  # По умолчанию ASIA
            self._settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
            
            # ЦВЕТА (обязательно должны быть!)
            self.theme_colors = {
                Theme.DARK: {
                    "bg_primary": "#1C1A17",
                    "bg_secondary": "#2A2723",
                    "text_primary": "#F0E9E0",
                    "text_secondary": "#A39E99",
                    "button_bg": "#4A4540",
                    "button_hover": "#2D2A27",
                    "button_text": "#F0E9E0",
                    "border": "#2A2723",
                    "accent": "#4A4540",
                },
                Theme.LIGHT: {
                    "bg_primary": "#F7F3EB",
                    "bg_secondary": "#F7F3EB",
                    "text_primary": "#3A322B",
                    "text_secondary": "#534941",
                    "button_bg": "#8F8A84",
                    "button_hover": "#68635D",
                    "button_text": "#3A322B",
                    "border": "#E8E0D3",
                    "accent": "#463F39",
                },
                Theme.ASIA: {
                    "bg_primary": "#1a237e",
                    "bg_secondary": "#283593",
                    "text_primary": "#ffffff",
                    "text_secondary": "#e0e0e0",
                    "button_bg": "#00bcd4",
                    "button_hover": "#00acc1",
                    "button_text": "#000000",
                    "border": "#3949ab",
                    "accent": "#00bcd4",
                },
            }
            
            self.load_settings() 

    @property
    def language(self):
        return self._language
    
    @language.setter
    def language(self, value):
        if isinstance(value, Language) and value != self._language:
            self._language = value
            self.save_settings()
            self.settings_changed.emit()

    @property
    def theme(self):
        return self._theme
    
    @theme.setter
    def theme(self, value):
        if isinstance(value, Theme) and value != self._theme:
            self._theme = value
            self.save_settings()
            print(f"Тема изменена на: {self._theme.value}")
            self.settings_changed.emit()        

    def get_color(self, color_name):
        return self.theme_colors.get(self._theme, {}).get(color_name, "#000000")
    
    def get_theme_stylesheet(self):
        """Старый метод - для совместимости"""
        colors = self.theme_colors.get(self._theme, self.theme_colors[Theme.DARK])
        
        return f"""
            QWidget {{
                background-color: {colors["bg_primary"]};
                color: {colors["text_primary"]};
            }}
            QPushButton {{
                background-color: {colors["button_bg"]};
                color: {colors["button_text"]};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {colors["button_hover"]};
            }}
            QPushButton:disabled {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_secondary"]};
            }}
            QLabel {{
                color: {colors["text_primary"]};
            }}
            QLineEdit, QTextEdit {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_primary"]};
                border: 1px solid {colors["border"]};
                border-radius: 3px;
                padding: 5px;
            }}
            QDialog {{
                background-color: {colors["bg_primary"]};
            }}
            QMenuBar {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_primary"]};
            }}
            QMenuBar::item:selected {{
                background-color: {colors["button_hover"]};
            }}
            QListWidget {{
                background-color: {colors["bg_secondary"]};
                color: {colors["text_primary"]};
                border: 1px solid {colors["border"]};
            }}
            QListWidget::item:selected {{
                background-color: {colors["button_bg"]};
            }}
        """           
    
    def get_text(self, key):
        texts = {
            "settings_title": {
                Language.ENGLISH: "Settings",
                Language.RUSSIAN: "Настройки"
            },
            "language_label": {
                Language.ENGLISH: "Language:",
                Language.RUSSIAN: "Язык:"
            },
            "theme_label": {
                Language.ENGLISH: "Theme:",
                Language.RUSSIAN: "Тема:"
            },
            "github_link": {
                Language.ENGLISH: "GitHub Repository",
                Language.RUSSIAN: "Репозиторий GitHub"
            },
            "close_button": {
                Language.ENGLISH: "Close",
                Language.RUSSIAN: "Закрыть"
            },
            "language_english": {
                Language.ENGLISH: "English",
                Language.RUSSIAN: "Английский"
            },
            "language_russian": {
                Language.ENGLISH: "Russian",
                Language.RUSSIAN: "Русский"
            },
            "theme_dark": {
                Language.ENGLISH: "Dark",
                Language.RUSSIAN: "Темная"
            },
            "theme_light": {
                Language.ENGLISH: "Light",
                Language.RUSSIAN: "Светлая"
            },
            "theme_blue": {
                Language.ENGLISH: "Asia",
                Language.RUSSIAN: "Азия"
            },
            "game_title": {
                Language.ENGLISH: "Go Game",
                Language.RUSSIAN: "Игра Го"
            },
            "pass_button": {
                Language.ENGLISH: "Pass",
                Language.RUSSIAN: "Пас"
            },
            "resign_button": {
                Language.ENGLISH: "Resign",
                Language.RUSSIAN: "Сдаться"
            },
            "resign_title": {
                Language.ENGLISH: "Resign",
                Language.RUSSIAN: "Сдаться"
            },
            "resign_confirm": {
                Language.ENGLISH: "Are you sure you want to resign?",
                Language.RUSSIAN: "Вы уверены, что хотите сдаться?"
            },
            "game_ended": {
                Language.ENGLISH: "Game Over",
                Language.RUSSIAN: "Игра окончена"
            },
            "opponent_won": {
                Language.ENGLISH: "You resigned. Opponent wins!",
                Language.RUSSIAN: "Вы сдались. Победил противник!"
            },
            "black": {
                Language.ENGLISH: "Black",
                Language.RUSSIAN: "Черные"
            },
            "white": {
                Language.ENGLISH: "White",
                Language.RUSSIAN: "Белые"
            },
            "open_online": {
                Language.ENGLISH: "Online Game",
                Language.RUSSIAN: "Онлайн игра"
            },
            "open_offline": {
                Language.ENGLISH: "Offline Game",
                Language.RUSSIAN: "Оффлайн игра"
            },
            "open_bot": {
                Language.ENGLISH: "Bot Game",
                Language.RUSSIAN: "Игра с ботом"
            },
            "open_instruction": {
                Language.ENGLISH: "Rules",
                Language.RUSSIAN: "Правила"
            },
            "open_account": {
                Language.ENGLISH: "Account",
                Language.RUSSIAN: "Аккаунт"
            },
            "rules_content": {
            Language.ENGLISH: """
            Rules of the Game of Go

            ## The beginning
            The game begins on an empty board, typically 9x9, 13x13, or 19x19.
            Two players (Black and White) take turns placing stones of their color on the board.
            Black plays first. You may place a stone on any empty intersection of the lines, even on the edge of the board.

            ## Liberties
            Points adjacent to a stone (left, right, above, and below, not diagonally) are called liberties.
            When all liberties of a stone are occupied by opponent’s stones, the stone is captured (removed from the board and given to the opponent).

            ## Groups
            Stones that are adjacent to each other (left, right, below, above) form a group. The liberties of a group are the liberties of all stones within it. 
            If all liberties of a group are filled by enemy stones, the entire group is captured and given to the opponent.

            ## Forbidden moves
            There are forbidden moves: suicidal moves — meaning that after making such a move, your group (or the single stone you place) would have no liberties. 
            However, a move that removes your group’s last liberty is allowed if it results in capturing an enemy group or stone(s).

            ## "Eyes"
            There is a shape called an eye. An eye is an empty intersection completely surrounded by stones of one color. 
            You cannot play inside an eye made by the opponent’s stones, because the stone placed there would be immediately captured. Again, you may play there only if it results in capturing opponent’s stones.

            ## "Immortal" groups
            It follows that a group with more than one eye in its formation cannot be captured (since it’s impossible to play inside an eye to remove the group’s liberties).

            ## The rule of Ko
            In Go, there is the Ko rule. It forbids repeating a board position that has already occurred. 
            Suppose we are in a situation where we can capture an opponent’s stone in one move (call this position 1). We capture it. 
            Immediately after this move, the opponent might have the chance to capture a stone in return, but if that revenge capture would return the board to position 1, they cannot make that move according to the Ko rule.

            ## Territory
            Now about the most important part: territory. In Go, most points are gained by capturing territory. 
            Your territory (empty intersections without stones) is considered yours if it is completely surrounded by your stones. You can invade enemy territory, forcing the opponent to reduce their territory.
            Enemy stones or groups that do not have two or more eyes and are inside your territory are considered dead (at the end of the game, they are removed from the board and added to your captures).

            ## The end of a game
            Now about how the game ends. On your turn, you are not required to place a stone; you may pass, and the turn passes to the opponent. 
            If both players pass or if no more moves are possible on the board, the game ends and territory counting begins.

            ## Score counting
            During counting, first, all stones and groups considered dead are removed from the board. Such stones increase the number of captured stones. 
            Each captured enemy stone gives you one point, and each empty intersection in your territory also gives you one point.

            ## Komi
            Since Black plays first, White receives a point advantage — this is called komi. Usually komi is 6.5 points, but other values can be agreed upon. 
            """,
            Language.RUSSIAN: """
            Правила игры в го

            ## Начало
            Игра начинается с пустой доски размером обычно 9х9, 13х13 или 19х19.
            Два игрока(черные и белые) ходят поочереди, ставя камни своего цвета на доску.
            Черные ходят первыми. Вы можете поставить камень на любое свободное пересечение линий,
            даже на то, которое у края.

            ## Дыхания
            Точки рядом с камнем(слева, справа, сверху и снизу, не наискосок) называют
            дыханиями или свободами. Когда все дыхания камня оказываются перекрыты(на них стоят камни противника) то
            камень попадает в плен(снимается с доски и уходит к проотивнику).

            ## Группы
            Соседние друг с другом камни(справа, слева, снизу и сверху)
            образуют группу. Дыхания группы - это дыхания всех камней, которые в неё входят, соответственно, если перекрыть все дыхания
            группе(занять их вражескими камнями), то вся группа снимается с доски и переходит к противнику.

            ## Запрещенные ходы
            Существуют ходы, которые запрещено делать: самоубийственные - это значит, что при совершении этого хода твоя группа(или одиночный камень, который ты поставишь этим ходу на доску) перестанет иметь дыхания.
            Хотя иногда ход, перекрывающий дыхания для собственной группы совершить можно: когда этот ход приведет к захвату вражеской группы или отдельного(ых) камня.

            ## "Глаза"
            Существует форма или фигура расстановки камней, которая называется глаз. Глаз - значит одно пустое поле, окруженное камнями одного цвета. В это поле нельзя ходить, так как камень, который туда будет поставлен, сразу снимется с доски и перейдет к противнику.
            (имеется ввиду, что нельзя ходить в глаз, построенный камнями противника). Опять же, в него ходить можно толлько в том случае, когда это приведет к захвату камней противника.

            ## "Бессмертные" группы
            Из этого следует, что группа, которая имеет больше одного глаза в своей конфигурации, не может быть съедена ника(невозможно в таком случае поставить камень в глаз, чтобы лишить группу противника дыханий).

            ## Правило Ко
            В го существует правило Ко. Оно запрещает повторять позицию, которая уже была на доске, одним ходом. 
            Допустим мы оказались в ситуации, когда можем захватить камень противника одним ходом(пусть это позиция 1) Мы его можем съесть. 
            У противника сразу после этого хода может появиться возможность съесть камень в ответ, но если эта возможность "отомстить" приведет к к повтору позиции 1, то он не сможет ей воспользоваться, согласно правилу Ко.

            ## Территория
            Теперь о самом главном: о территории. В го большая часть очков набирается путем захвата территории. Вашей территория(пустые поля, на которых нет камней) назывется, если она полностью окружена вашими камнями. Во вражескую территорию можно вторгаться, заставляя противника уменьшить его территорию.
            Камни и группы противника, если у них нет двух и более глаз, которые находятся на вашей территории, считаются мертвыми(при завершении игры снимутся с доски и перейдут к вам).

            ## Конец игры
            Теперь о том, как игра заканчивается. В свой ход вы не обязаны ставить камень на поле, вы можете спасовать, тогда ход перейдет к противнику. 
            Если оба игрока спасуют или возможные ходы на доске закончатся, то партия завершается и начинается подсчет территории.

            ## Подсчет очков
            При подсчете территории сначала с доски снимаются все камни и группы, которые считаются мертвыми. Такие камни пополняют число захваченных камней. 
            Каждый вражеский захваченный камень даёт вам одно очко и каждое поле в вашей территории тоже дает вам одно очко.

            ## Коми
            Так как начинают игру черные, белые получают преимущество в очках - это называется коми. Обычно коми составляет 6.5 очков, но можно договориться и о других вариантах. 
        """
        },
                # ===== ONLINE LOBBY (online_lobby.py) =====
        "create_room_title": {
            Language.ENGLISH: "Create Online Room",
            Language.RUSSIAN: "Создание онлайн-комнаты",
        },
        "board_size_label": {
            Language.ENGLISH: "Board size:",
            Language.RUSSIAN: "Размер доски:",
        },
        "board_9x9": {
            Language.ENGLISH: "9×9",
            Language.RUSSIAN: "9×9",
        },
        "board_13x13": {
            Language.ENGLISH: "13×13",
            Language.RUSSIAN: "13×13",
        },
        "board_19x19": {
            Language.ENGLISH: "19×19",
            Language.RUSSIAN: "19×19",
        },
        "main_time_label": {
            Language.ENGLISH: "Main time:",
            Language.RUSSIAN: "Основное время:",
        },
        "byoyomi_label": {
            Language.ENGLISH: "Byoyomi:",
            Language.RUSSIAN: "Бёёми:",
        },
        "no_time_limit": {
            Language.ENGLISH: "No time limit",
            Language.RUSSIAN: "Без лимита времени",
        },
        "show_legal_moves": {
            Language.ENGLISH: "Show legal moves",
            Language.RUSSIAN: "Показывать разрешённые ходы",
        },
        "room_password_label": {
            Language.ENGLISH: "Room password:",
            Language.RUSSIAN: "Пароль комнаты:",
        },
        "password_placeholder": {
            Language.ENGLISH: "leave empty for open room",
            Language.RUSSIAN: "оставьте пустым для открытой комнаты",
        },
        "online_game_title": {
            Language.ENGLISH: "Online Game",
            Language.RUSSIAN: "Сетевая игра",
        },
        "create_room_button": {
            Language.ENGLISH: "Create Room",
            Language.RUSSIAN: "Создать комнату",
        },
        "join_room_button": {
            Language.ENGLISH: "Join Room",
            Language.RUSSIAN: "Присоединиться к комнате",
        },
        "refresh_button": {
            Language.ENGLISH: "Refresh list",
            Language.RUSSIAN: "Обновить список",
        },
        "join_selected_button": {
            Language.ENGLISH: "Join selected",
            Language.RUSSIAN: "Войти в выбранную",
        },
        "back_button": {
            Language.ENGLISH: "Back",
            Language.RUSSIAN: "Назад",
        },
        "room_label": {
            Language.ENGLISH: "Room:",
            Language.RUSSIAN: "Комната:",
        },
        "ready_button": {
            Language.ENGLISH: "Ready",
            Language.RUSSIAN: "Готов",
        },
        "waiting_opponent": {
            Language.ENGLISH: "Waiting for opponent...",
            Language.RUSSIAN: "Ожидание соперника...",
        },
        "leave_room_button": {
            Language.ENGLISH: "Leave room",
            Language.RUSSIAN: "Покинуть комнату",
        },
        "chat_placeholder": {
            Language.ENGLISH: "Message...",
            Language.RUSSIAN: "Сообщение...",
        },
        "send_button": {
            Language.ENGLISH: "Send",
            Language.RUSSIAN: "Отправить",
        },
        "password_dialog_title": {
            Language.ENGLISH: "Password",
            Language.RUSSIAN: "Пароль",
        },
        "password_dialog_label": {
            Language.ENGLISH: "Enter room password:",
            Language.RUSSIAN: "Введите пароль комнаты:",
        },
        "attention": {
            Language.ENGLISH: "Attention",
            Language.RUSSIAN: "Внимание",
        },
        "select_room_warning": {
            Language.ENGLISH: "Select a room from the list",
            Language.RUSSIAN: "Выберите комнату из списка",
        },
        "connection_lost": {
            Language.ENGLISH: "Connection lost to server",
            Language.RUSSIAN: "Потеряно соединение с сервером",
        },
        "connection": {
            Language.ENGLISH: "Connection",
            Language.RUSSIAN: "Соединение",
        },

        # ===== GAME WINDOW ONLINE (game_windowOnline.py) =====
        "leave_lobby_button": {
            Language.ENGLISH: "Leave lobby",
            Language.RUSSIAN: "Выйти из лобби",
        },
        "time_expired_title": {
            Language.ENGLISH: "Time expired",
            Language.RUSSIAN: "Время вышло",
        },
        "time_expired_message": {
            Language.ENGLISH: "{} exceeded time limit. {} wins!",
            Language.RUSSIAN: "{} превысили лимит времени. Победили {}.",
        },
        "resign_confirm_message": {
            Language.ENGLISH: "Are you sure?",
            Language.RUSSIAN: "Вы уверены?",
        },
        "game_analysis_progress": {
            Language.ENGLISH: "Analyzing position...",
            Language.RUSSIAN: "Анализируем позицию...",
        },
        "analysis_error_title": {
            Language.ENGLISH: "Analysis error",
            Language.RUSSIAN: "Ошибка анализа",
        },
        "analysis_error_message": {
            Language.ENGLISH: "Error analyzing game:\n{}\nGame finished without analysis.",
            Language.RUSSIAN: "Ошибка при анализе партии:\n{}\nИгра завершена без анализа.",
        },
        "two_passes_finished": {
            Language.ENGLISH: "Two passes! Game finished.",
            Language.RUSSIAN: "Два паса! Игра завершена.",
        },
        "analysis_unavailable": {
            Language.ENGLISH: "Game finished by two passes.\nAnalysis unavailable: game too short.",
            Language.RUSSIAN: "Игра завершена двумя пасами.\nАнализ недоступен: слишком короткая партия.",
        },
        "winner_label": {
            Language.ENGLISH: "Winner: {}",
            Language.RUSSIAN: "Победитель: {}",
        },
        "margin_label": {
            Language.ENGLISH: "Margin: {:.1f} points",
            Language.RUSSIAN: "Отрыв: {:.1f} очков",
        },
        "black_color": {
            Language.ENGLISH: "Black",
            Language.RUSSIAN: "Чёрные",
        },
        "white_color": {
            Language.ENGLISH: "White",
            Language.RUSSIAN: "Белые",
        },

        # ===== Дополнительные сообщения об ошибках (network_client_wrapper) =====
        "error_prefix": {
            Language.ENGLISH: "Error",
            Language.RUSSIAN: "Ошибка",
        },
            "Close": {
            Language.ENGLISH: "Close",
            Language.RUSSIAN: "Закрыть"
        },
        }
        return texts.get(key, {}).get(self._language, key)
    
    # ========== ГЛАВНЫЙ МЕТОД - ЗАГРУЗКА QSS ФАЙЛОВ ==========
    def get_stylesheet(self):
        """Загружает QSS файл для текущей темы"""
        
        # Определяем имя файла по теме
        theme_files = {
            Theme.DARK: "dark.qss",
            Theme.LIGHT: "light.qss",
            Theme.ASIA: "asia.qss"
        }
        
        theme_file = theme_files.get(self._theme, "dark.qss")
        
        # Путь к папке themes (на уровень выше windows)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        qss_path = os.path.join(base_dir, "themes", theme_file)
        
        print(f"Загрузка темы: {self._theme.value}")
        print(f"Путь к QSS: {qss_path}")
        
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    print(f"✓ QSS файл загружен, размер: {len(content)} символов")
                    return content
            except Exception as e:
                print(f"✗ Ошибка чтения QSS: {e}")
        else:
            print(f"✗ QSS файл не найден: {qss_path}")
            # Покажем содержимое папки themes для отладки
            themes_dir = os.path.dirname(qss_path)
            if os.path.exists(themes_dir):
                print(f"Содержимое папки themes: {os.listdir(themes_dir)}")
        
        # Если QSS файл не найден, используем встроенные стили
        print("→ Использую встроенные стили (get_theme_stylesheet)")
        return self.get_theme_stylesheet()
    
    def save_settings(self):
        settings_data = {
            "language": self._language.value,
            "theme": self._theme.value
        }
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        if os.path.exists(self._settings_file):
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                if "language" in settings_data:
                    lang_value = settings_data["language"]
                    if lang_value == "ru":
                        self._language = Language.RUSSIAN
                    elif lang_value == "en":
                        self._language = Language.ENGLISH
                
                if "theme" in settings_data:
                    theme_value = settings_data["theme"]
                    if theme_value == "light":
                        self._theme = Theme.LIGHT
                    elif theme_value == "dark":
                        self._theme = Theme.DARK
                    elif theme_value == "asia":
                        self._theme = Theme.ASIA
                        
            except Exception as e:
                print(f"Error loading settings: {e}")

    def get_icon_path(self, icon_name):

        theme_folders = {
            Theme.DARK: "light",
            Theme.LIGHT: "dark",
            Theme.ASIA: "dark"
        }
        
        theme_folder = theme_folders.get(self._theme, "light")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "icons", theme_folder, f"{icon_name}.svg")
        
        if os.path.exists(icon_path):
            print(f"✓ Иконка найдена: {icon_path}")
            return icon_path
        else:
            print(f"✗ Иконка не найдена: {icon_path}")
            return ""            