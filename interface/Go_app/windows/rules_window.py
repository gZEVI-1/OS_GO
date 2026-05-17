from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from windows.base_window import BaseWindow
from generated.ui_rules import Ui_RulesDialog


class RulesWindow(BaseWindow):
    def __init__(self, navigation, parent=None):
        super().__init__(navigation, parent)
        
        self.ui = Ui_RulesDialog()
        self.ui.setupUi(self)
        
        self.ui.textBrowser.setOpenExternalLinks(False)
        self.ui.textBrowser.anchorClicked.connect(self._handle_link_click)
        
        self.ui.buttonClose.setText("Close")
        self.ui.buttonClose.clicked.connect(self.go_back_to_menu)
        
        self.update_language()
    
    def _handle_link_click(self, url: QUrl):
        QDesktopServices.openUrl(url)
    
    def go_back_to_menu(self):
        """Возврат в главное меню"""
        self.navigation.navigate_to("main_menu")
    
    def update_language(self):
        self.setWindowTitle(self.settings.get_text("Rules"))
        self.ui.buttonClose.setText(self.settings.get_text("Close"))