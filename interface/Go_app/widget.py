# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QWidget, QMessageBox

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_mainWindow

class Widget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        self.ui.buttonWindOffline.clicked.connect(self.open_windOffline)
        self.ui.buttonWindOnline.clicked.connect(self.open_windOnline)
        self.ui.buttonWindBot.clicked.connect(self.open_windBot)
        self.ui.buttonInstruct.clicked.connect(self.open_windInstruct)

        self.ui.buttonAccount.clicked.connect(self.open_windAccount)
        self.ui.buttonSettings.clicked.connect(self.open_windSettings)

    def open_windOffline(self):
        print("Offline button on the main window")
        QMessageBox.information(self,"Button", "open offline window")

    def open_windOnline(self):
        print("Online button on the main window")
        QMessageBox.information(self,"Button", "open online window")

    def open_windBot(self):
        print("Bot button on the main window")
        QMessageBox.information(self,"Button", "open bot window")

    def open_windInstruct(self):
        print("Instruction button on the main window")
        QMessageBox.information(self,"Button", "open instruction window")

    def open_windAccount(self):
        print("Account button on the sidebar")
        QMessageBox.information(self,"Button", "open account window")

    def open_windSettings(self):
        print("Settings button on the sidebar")
        QMessageBox.information(self,"Button", "open settings window")






if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
