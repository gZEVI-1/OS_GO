# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_settings_dialog_pve.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
    QHBoxLayout, QPushButton, QRadioButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_GameSettingsDialogPVE(object):
    def setupUi(self, GameSettingsDialogPVE):
        if not GameSettingsDialogPVE.objectName():
            GameSettingsDialogPVE.setObjectName(u"GameSettingsDialogPVE")
        GameSettingsDialogPVE.resize(450, 350)
        self.verticalLayout = QVBoxLayout(GameSettingsDialogPVE)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBoardSize = QGroupBox(GameSettingsDialogPVE)
        self.groupBoardSize.setObjectName(u"groupBoardSize")
        self.verticalLayout_2 = QVBoxLayout(self.groupBoardSize)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.radio9x9 = QRadioButton(self.groupBoardSize)
        self.radio9x9.setObjectName(u"radio9x9")
        self.radio9x9.setChecked(True)

        self.verticalLayout_2.addWidget(self.radio9x9)

        self.radio13x13 = QRadioButton(self.groupBoardSize)
        self.radio13x13.setObjectName(u"radio13x13")

        self.verticalLayout_2.addWidget(self.radio13x13)

        self.radio19x19 = QRadioButton(self.groupBoardSize)
        self.radio19x19.setObjectName(u"radio19x19")

        self.verticalLayout_2.addWidget(self.radio19x19)


        self.verticalLayout.addWidget(self.groupBoardSize)

        self.groupPlayerColor = QGroupBox(GameSettingsDialogPVE)
        self.groupPlayerColor.setObjectName(u"groupPlayerColor")
        self.verticalLayout_3 = QVBoxLayout(self.groupPlayerColor)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.radioBlack = QRadioButton(self.groupPlayerColor)
        self.radioBlack.setObjectName(u"radioBlack")
        self.radioBlack.setChecked(True)

        self.verticalLayout_3.addWidget(self.radioBlack)

        self.radioWhite = QRadioButton(self.groupPlayerColor)
        self.radioWhite.setObjectName(u"radioWhite")

        self.verticalLayout_3.addWidget(self.radioWhite)


        self.verticalLayout.addWidget(self.groupPlayerColor)

        self.groupVisual = QGroupBox(GameSettingsDialogPVE)
        self.groupVisual.setObjectName(u"groupVisual")
        self.verticalLayout_4 = QVBoxLayout(self.groupVisual)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.checkLegalMoves = QCheckBox(self.groupVisual)
        self.checkLegalMoves.setObjectName(u"checkLegalMoves")
        self.checkLegalMoves.setChecked(True)

        self.verticalLayout_4.addWidget(self.checkLegalMoves)


        self.verticalLayout.addWidget(self.groupVisual)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonOk = QPushButton(GameSettingsDialogPVE)
        self.buttonOk.setObjectName(u"buttonOk")

        self.horizontalLayout.addWidget(self.buttonOk)

        self.buttonCancel = QPushButton(GameSettingsDialogPVE)
        self.buttonCancel.setObjectName(u"buttonCancel")

        self.horizontalLayout.addWidget(self.buttonCancel)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(GameSettingsDialogPVE)

        self.buttonOk.setDefault(True)


        QMetaObject.connectSlotsByName(GameSettingsDialogPVE)
    # setupUi

    def retranslateUi(self, GameSettingsDialogPVE):
        GameSettingsDialogPVE.setWindowTitle(QCoreApplication.translate("GameSettingsDialogPVE", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0438\u0433\u0440\u044b \u0441 \u0431\u043e\u0442\u043e\u043c", None))
        self.groupBoardSize.setTitle(QCoreApplication.translate("GameSettingsDialogPVE", u"\u0420\u0430\u0437\u043c\u0435\u0440 \u0434\u043e\u0441\u043a\u0438", None))
        self.groupBoardSize.setStyleSheet(QCoreApplication.translate("GameSettingsDialogPVE", u"QGroupBox {\n"
"    font-weight: bold;\n"
"    margin-top: 10px;\n"
"}\n"
"QGroupBox::title {\n"
"    subcontrol-origin: margin;\n"
"    left: 10px;\n"
"    padding: 0 5px 0 5px;\n"
"}", None))
        self.radio9x9.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"9x9 (\u043c\u0430\u043b\u0430\u044f)", None))
        self.radio13x13.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"13x13 (\u0441\u0440\u0435\u0434\u043d\u044f\u044f)", None))
        self.radio19x19.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"19x19 (\u0441\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u0430\u044f)", None))
        self.groupPlayerColor.setTitle(QCoreApplication.translate("GameSettingsDialogPVE", u"\u0426\u0432\u0435\u0442 \u0438\u0433\u0440\u043e\u043a\u0430", None))
        self.radioBlack.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"\u0427\u0435\u0440\u043d\u044b\u0435 (\u0445\u043e\u0434\u044f\u0442 \u043f\u0435\u0440\u0432\u044b\u043c\u0438)", None))
        self.radioWhite.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"\u0411\u0435\u043b\u044b\u0435 (\u0445\u043e\u0434\u044f\u0442 \u0432\u0442\u043e\u0440\u044b\u043c\u0438)", None))
        self.groupVisual.setTitle(QCoreApplication.translate("GameSettingsDialogPVE", u"\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\u0438", None))
        self.checkLegalMoves.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"\u041f\u043e\u0434\u0441\u0432\u0435\u0447\u0438\u0432\u0430\u0442\u044c \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u0445\u043e\u0434\u044b", None))
        self.buttonOk.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"\u041d\u0430\u0447\u0430\u0442\u044c \u0438\u0433\u0440\u0443", None))
        self.buttonOk.setStyleSheet(QCoreApplication.translate("GameSettingsDialogPVE", u"QPushButton {\n"
"    background-color: #4CAF50;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 8px 20px;\n"
"    border-radius: 4px;\n"
"    font-weight: bold;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #45a049;\n"
"}", None))
        self.buttonCancel.setText(QCoreApplication.translate("GameSettingsDialogPVE", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
        self.buttonCancel.setStyleSheet(QCoreApplication.translate("GameSettingsDialogPVE", u"QPushButton {\n"
"    background-color: #f44336;\n"
"    color: white;\n"
"    border: none;\n"
"    padding: 8px 20px;\n"
"    border-radius: 4px;\n"
"    font-weight: bold;\n"
"}\n"
"QPushButton:hover {\n"
"    background-color: #da190b;\n"
"}", None))
    # retranslateUi

