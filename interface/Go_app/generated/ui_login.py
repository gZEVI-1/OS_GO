# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QPushButton, QSizePolicy,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(751, 543)
        Dialog.setStyleSheet(u"QPushButton#loginButton{\n"
"    background-color: #4CAF50;\n"
"    border-radius: 12px;  \n"
"    color: white;\n"
"}")
        self.guestButton = QPushButton(Dialog)
        self.guestButton.setObjectName(u"guestButton")
        self.guestButton.setGeometry(QRect(290, 200, 161, 61))
        self.guestButton.setStyleSheet(u"QPushButton#guestButton{\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"}")
        self.loginButton = QPushButton(Dialog)
        self.loginButton.setObjectName(u"loginButton")
        self.loginButton.setGeometry(QRect(290, 270, 161, 61))
        self.loginButton.setStyleSheet(u"QPushButton#loginButton{\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"}")

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.guestButton.setText(QCoreApplication.translate("Dialog", u"openMainWind", None))
        self.loginButton.setText(QCoreApplication.translate("Dialog", u"openLoginWind", None))
    # retranslateUi

