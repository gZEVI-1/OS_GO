import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Signal

class ProfileWindow(QDialog):
    profile_updated = Signal(dict)

    def __init__(self, user_data, parent=None):
        super().__init__(parent)

        # Загружаем UI из файла
        loader = QUiLoader()
        ui_file_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'profile_window.ui')
        ui_file = QFile(ui_file_path)
        ui_file.open(QFile.ReadOnly)
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        if not self.ui:
            raise RuntimeError("Не удалось загрузить profile_window.ui")

        self.user_data = user_data
        self.setup_ui()
        self.connect_signals()
        self.setModal(True)

    def setup_ui(self):
        name = self.user_data.get('full_name', self.user_data.get('email', 'Пользователь'))
        self.ui.userNameLabel.setText(name)
        self.ui.emailLabel.setText(self.user_data.get('email', ''))
        self.ui.avatarButton.setText("👤")
        self.ui.avatarButton.setEnabled(False)   # пока без выбора аватара

    def connect_signals(self):
        self.ui.statsButton.clicked.connect(self.on_stats_click)
        self.ui.editProfileButton.clicked.connect(self.on_edit_profile_click)

    def on_stats_click(self):
        QMessageBox.information(self, "Статистика",
                                "Игр сыграно: 0\nПобед: 0\nПоражений: 0\nРейтинг: 1000")

    def on_edit_profile_click(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование профиля")
        dialog.setModal(True)
        dialog.setMinimumWidth(350)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        name_edit = QLineEdit(self.user_data.get('full_name', ''))
        name_edit.setPlaceholderText("Имя пользователя")
        form.addRow("Имя:", name_edit)
        layout.addLayout(form)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(lambda: self._save_profile(name_edit.text(), dialog))
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)

        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        dialog.exec()

    def _save_profile(self, new_name, dialog):
        if new_name and new_name != self.user_data.get('full_name', ''):
            self.user_data['full_name'] = new_name
            self.ui.userNameLabel.setText(new_name)
            self.profile_updated.emit(self.user_data)
            QMessageBox.information(self, "Успех", "Имя обновлено")
        dialog.accept()