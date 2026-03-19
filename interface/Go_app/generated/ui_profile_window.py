# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'profile_window.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_profile_window(object):
    def setupUi(self, profile_window):
        if not profile_window.objectName():
            profile_window.setObjectName(u"profile_window")
        profile_window.resize(156, 250)
        profile_window.setStyleSheet(u"QDialog {\n"
"    background-color: white;\n"
"    border: 2px solid #4CAF50;\n"
"    border-radius: 10px;\n"
"}\n"
"\n"
"QLabel#avatarLabel {\n"
"    border: 2px solid #4CAF50;\n"
"    border-radius: 25px;\n"
"\n"
"}\n"
"\n"
"QPushButton#closeButton {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 5px;\n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"    font-weight: bold;\n"
"    min-width: 100px;\n"
"}\n"
"\n"
"QPushButton#buttonClose:hover {\n"
"    background-color: #45a049;\n"
"}")
        self.avatarLabel = QLabel(profile_window)
        self.avatarLabel.setObjectName(u"avatarLabel")
        self.avatarLabel.setGeometry(QRect(50, 10, 51, 51))
        self.nameLabel = QLabel(profile_window)
        self.nameLabel.setObjectName(u"nameLabel")
        self.nameLabel.setGeometry(QRect(20, 70, 111, 20))
        self.ratingLabel = QLabel(profile_window)
        self.ratingLabel.setObjectName(u"ratingLabel")
        self.ratingLabel.setGeometry(QRect(20, 100, 111, 20))
        self.winsLabel = QLabel(profile_window)
        self.winsLabel.setObjectName(u"winsLabel")
        self.winsLabel.setGeometry(QRect(20, 130, 111, 20))
        self.lossesLabel = QLabel(profile_window)
        self.lossesLabel.setObjectName(u"lossesLabel")
        self.lossesLabel.setGeometry(QRect(20, 160, 111, 20))
        self.countryLabel = QLabel(profile_window)
        self.countryLabel.setObjectName(u"countryLabel")
        self.countryLabel.setGeometry(QRect(20, 190, 111, 20))
        self.buttonClose = QPushButton(profile_window)
        self.buttonClose.setObjectName(u"buttonClose")
        self.buttonClose.setGeometry(QRect(92, 218, 51, 21))

        self.retranslateUi(profile_window)

        QMetaObject.connectSlotsByName(profile_window)
    # setupUi

    def retranslateUi(self, profile_window):
        profile_window.setWindowTitle(QCoreApplication.translate("profile_window", u"Dialog", None))
        self.avatarLabel.setText(QCoreApplication.translate("profile_window", u"avatarLabel", None))
        self.nameLabel.setText(QCoreApplication.translate("profile_window", u"nameLabel", None))
        self.ratingLabel.setText(QCoreApplication.translate("profile_window", u"ratingLabel", None))
        self.winsLabel.setText(QCoreApplication.translate("profile_window", u"winsLabel", None))
        self.lossesLabel.setText(QCoreApplication.translate("profile_window", u"lossesLabel", None))
        self.countryLabel.setText(QCoreApplication.translate("profile_window", u"countryLabel", None))
        self.buttonClose.setText(QCoreApplication.translate("profile_window", u"Close", None))
    # retranslateUi

