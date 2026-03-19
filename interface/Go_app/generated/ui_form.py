# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDockWidget, QPushButton, QSizePolicy,
    QWidget)

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        if not mainWindow.objectName():
            mainWindow.setObjectName(u"mainWindow")
        mainWindow.resize(751, 543)
        self.sidebar = QDockWidget(mainWindow)
        self.sidebar.setObjectName(u"sidebar")
        self.sidebar.setGeometry(QRect(0, -30, 61, 571))
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.buttonAccount = QPushButton(self.dockWidgetContents)
        self.buttonAccount.setObjectName(u"buttonAccount")
        self.buttonAccount.setGeometry(QRect(10, 30, 40, 40))
        self.buttonAccount.setStyleSheet(u"QPushButton#buttonAccount{\n"
"    background-color: #1A1A1A;\n"
"    border-radius: 20px;\n"
"    min-width: 40px;\n"
"    min-height: 40px;\n"
"    max-width: 40px;\n"
"    max-height: 40px;\n"
"    color: white;\n"
"\n"
"}")
        self.buttonSettings = QPushButton(self.dockWidgetContents)
        self.buttonSettings.setObjectName(u"buttonSettings")
        self.buttonSettings.setGeometry(QRect(10, 480, 40, 40))
        self.buttonSettings.setStyleSheet(u"QPushButton {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"}")
        icon = QIcon()
        icon.addFile(u"C:/Users/polin/Downloads/pngegg.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.buttonSettings.setIcon(icon)
        self.buttonSettings.setIconSize(QSize(30, 30))
        self.sidebar.setWidget(self.dockWidgetContents)
        self.buttonWindOnline = QPushButton(mainWindow)
        self.buttonWindOnline.setObjectName(u"buttonWindOnline")
        self.buttonWindOnline.setGeometry(QRect(310, 150, 171, 141))
        self.buttonWindOnline.setStyleSheet(u"QPushButton#buttonWindOnline {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"}")
        self.buttonWindOffline = QPushButton(mainWindow)
        self.buttonWindOffline.setObjectName(u"buttonWindOffline")
        self.buttonWindOffline.setGeometry(QRect(110, 150, 171, 141))
        self.buttonWindOffline.setStyleSheet(u"QPushButton#buttonWindOffline{\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"}")
        self.buttonInstruct = QPushButton(mainWindow)
        self.buttonInstruct.setObjectName(u"buttonInstruct")
        self.buttonInstruct.setGeometry(QRect(170, 310, 451, 41))
        self.buttonInstruct.setStyleSheet(u"QPushButton#buttonInstruct {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 2.5px;\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")
        self.buttonWindBot = QPushButton(mainWindow)
        self.buttonWindBot.setObjectName(u"buttonWindBot")
        self.buttonWindBot.setGeometry(QRect(510, 150, 171, 141))
        self.buttonWindBot.setStyleSheet(u"QPushButton#buttonWindBot {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"}")

        self.retranslateUi(mainWindow)

        QMetaObject.connectSlotsByName(mainWindow)
    # setupUi

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(QCoreApplication.translate("mainWindow", u"Widget", None))
        self.buttonAccount.setText(QCoreApplication.translate("mainWindow", u"account", None))
        self.buttonWindOnline.setText(QCoreApplication.translate("mainWindow", u"openOnline", None))
        self.buttonWindOffline.setText(QCoreApplication.translate("mainWindow", u"openOffline", None))
        self.buttonInstruct.setText(QCoreApplication.translate("mainWindow", u"openInstruct", None))
        self.buttonWindBot.setText(QCoreApplication.translate("mainWindow", u"openBot", None))
    # retranslateUi

