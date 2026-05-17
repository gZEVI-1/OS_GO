import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QMessageBox
from PySide6.QtCore import Qt

current_dir = os.path.dirname(os.path.abspath(__file__))
auth_path = os.path.join(current_dir, "auth", "app", "desktop")
interface_path = os.path.join(current_dir, "interface", "Go_app")

sys.path.insert(0, auth_path)
sys.path.insert(0, interface_path)

from auth.app.desktop.main import AuthWindow
from interface.Go_app.widget import Widget

class AppManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OS_GO Game")
        self.setMinimumSize(1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Стек для переключения окон
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Создаем окна
        self.auth_window = AuthWindow()
        self.game_window = None
        
        # Добавляем окно аутентификации в стек
        self.stacked_widget.addWidget(self.auth_window)
        
        # Подменяем метод show_profile для перехвата авторизации
        self.original_show_profile = self.auth_window.show_profile
        self.auth_window.show_profile = self.on_auth_success
        
        # Показываем окно аутентификации
        self.stacked_widget.setCurrentWidget(self.auth_window)
        
        # Центрируем окно
        self.center_window()

    def on_auth_success(self):
        try:
            import requests
            
            # Получаем данные пользователя
            response = requests.get(
                "http://51.250.64.161:8000/auth/me",
                headers={"Authorization": f"Bearer {self.auth_window.token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                email = user_data.get('email', '')
                
                # Определяем флаги пользователя
                is_guest = email.endswith('@osgo.local')
                
                # Создаем словарь с флагами для передачи в игровое окно
                user_flags = {
                    'is_guest': is_guest,
                    'is_registered': not is_guest,
                    'email': email,
                    'token': self.auth_window.token,
                    'totp_enabled': user_data.get('totp_enabled', False),
                    'can_change_password': not is_guest,
                    'can_use_2fa': not is_guest,
                    'can_delete_account': not is_guest,
                    'can_play_online': True,
                    'can_play_with_bot': True,
                    'can_view_profile': True
                }
                
                print(f"[AppManager] Пользователь авторизован: {email}")
                print(f"[AppManager] Тип: {'Гость' if is_guest else 'Зарегистрированный'}")
                
                # Создаем игровое окно с флагами
                self.create_game_window(user_flags)
                
                # Переключаемся на игровое окно
                self.stacked_widget.addWidget(self.game_window)
                self.stacked_widget.setCurrentWidget(self.game_window)    

        except Exception as e:
            print(f"[AppManager] Ошибка при получении данных: {e}")
            # В случае ошибки показываем оригинальный профиль
            self.original_show_profile()

    def create_game_window(self, user_flags):
        self.game_window = Widget()
        
        # Сохраняем флаги в игровом окне
        self.game_window.user_flags = user_flags
        
        # Сохраняем оригинальные методы
        if not hasattr(self.game_window, 'original_open_account'):
            self.game_window.original_open_account = self.game_window.open_windAccount
        
        # Подменяем метод открытия аккаунта
        self.game_window.open_windAccount = lambda: self.custom_open_account(user_flags)
        
        # Добавляем методы для проверки флагов
        self.game_window.get_user_flag = lambda flag: user_flags.get(flag, False)
        self.game_window.is_guest = lambda: user_flags.get('is_guest', False)
        self.game_window.is_registered = lambda: user_flags.get('is_registered', False)
        
        # Обновляем UI в зависимости от флагов
        self.update_game_ui_by_flags()
    
    def update_game_ui_by_flags(self):
        """Обновляет интерфейс игрового окна согласно флагам"""
        if not self.game_window or not hasattr(self.game_window, 'user_flags'):
            return
        
        flags = self.game_window.user_flags
        
        # Меняем текст кнопки аккаунта для гостя
        if hasattr(self.game_window.ui, 'buttonAccount'):
            if flags.get('is_guest'):
                self.game_window.ui.buttonAccount.setText("👤 Гость")
                self.game_window.ui.buttonAccount.setToolTip(
                    "Гостевой аккаунт. Для полного доступа зарегистрируйтесь."
                )
            else:
                self.game_window.ui.buttonAccount.setText("👤 Аккаунт")
                self.game_window.ui.buttonAccount.setToolTip(
                    "Управление аккаунтом"
                )
    
    def custom_open_account(self, user_flags):
        """Кастомное открытие окна аккаунта с учетом флагов"""
        if user_flags.get('is_guest'):
            # Для гостя показываем информационное сообщение
            msg = QMessageBox(self.game_window)
            msg.setWindowTitle("Гостевой аккаунт")
            msg.setText("Вы играете как гость")
            msg.setInformativeText(
                "Доступные возможности:\n"
                "✓ Играть онлайн\n"
                "✓ Играть с ботом\n"
                "✓ Смотреть правила\n\n"
                "❌ Недоступно:\n"
                "❌ Смена пароля\n"
                "❌ Настройка 2FA\n"
                "❌ Удаление аккаунта\n\n"
                "📝 Зарегистрируйтесь для полного доступа!"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        else:
            # Для зарегистрированного пользователя показываем полную информацию
            msg = QMessageBox(self.game_window)
            msg.setWindowTitle("Профиль пользователя")
            msg.setText(f"👤 {user_flags.get('email', 'Unknown')}")
            msg.setInformativeText(
                f"Тип: Зарегистрированный пользователь\n"
                f"2FA: {'✅ Включена' if user_flags.get('totp_enabled') else '❌ Выключена'}\n\n"
                "Доступные возможности:\n"
                "✅ Смена пароля\n"
                "✅ Настройка 2FA\n"
                "✅ Управление аккаунтом\n"
                "✅ Играть онлайн\n"
                "✅ Играть с ботом\n\n"
                "🔧 Дополнительные функции в разработке"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = AppManager()
    manager.show()
    sys.exit(app.exec())            
