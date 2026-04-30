# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_settings_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_GameSettingsDialog(object):
    def setupUi(self, GameSettingsDialog):
        if not GameSettingsDialog.objectName():
            GameSettingsDialog.setObjectName(u"GameSettingsDialog")
        GameSettingsDialog.resize(400, 427)
        self.verticalLayout = QVBoxLayout(GameSettingsDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBoardSize = QGroupBox(GameSettingsDialog)
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

        self.groupTime = QGroupBox(GameSettingsDialog)
        self.groupTime.setObjectName(u"groupTime")
        self.gridLayout = QGridLayout(self.groupTime)
        self.gridLayout.setObjectName(u"gridLayout")
        self.labelPlayerTime = QLabel(self.groupTime)
        self.labelPlayerTime.setObjectName(u"labelPlayerTime")

        self.gridLayout.addWidget(self.labelPlayerTime, 0, 0, 1, 1)

        self.spinPlayerTime = QSpinBox(self.groupTime)
        self.spinPlayerTime.setObjectName(u"spinPlayerTime")
        self.spinPlayerTime.setMinimum(1)
        self.spinPlayerTime.setMaximum(60)
        self.spinPlayerTime.setValue(15)

        self.gridLayout.addWidget(self.spinPlayerTime, 0, 1, 1, 1)

        self.labelByoyomi = QLabel(self.groupTime)
        self.labelByoyomi.setObjectName(u"labelByoyomi")

        self.gridLayout.addWidget(self.labelByoyomi, 1, 0, 1, 1)

        self.spinByoyomi = QSpinBox(self.groupTime)
        self.spinByoyomi.setObjectName(u"spinByoyomi")
        self.spinByoyomi.setMinimum(0)
        self.spinByoyomi.setMaximum(60)
        self.spinByoyomi.setValue(30)

        self.gridLayout.addWidget(self.spinByoyomi, 1, 1, 1, 1)


        self.verticalLayout.addWidget(self.groupTime)

        self.groupAI = QGroupBox(GameSettingsDialog)
        self.groupAI.setObjectName(u"groupAI")
        self.verticalLayout_3 = QVBoxLayout(self.groupAI)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.checkLegalMoves = QCheckBox(self.groupAI)
        self.checkLegalMoves.setObjectName(u"checkLegalMoves")
        self.checkLegalMoves.setChecked(True)

        self.verticalLayout_3.addWidget(self.checkLegalMoves)


        self.verticalLayout.addWidget(self.groupAI)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonOk = QPushButton(GameSettingsDialog)
        self.buttonOk.setObjectName(u"buttonOk")

        self.horizontalLayout.addWidget(self.buttonOk)

        self.buttonCancel = QPushButton(GameSettingsDialog)
        self.buttonCancel.setObjectName(u"buttonCancel")

        self.horizontalLayout.addWidget(self.buttonCancel)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(GameSettingsDialog)

        self.buttonOk.setDefault(True)


        QMetaObject.connectSlotsByName(GameSettingsDialog)
    # setupUi

    def retranslateUi(self, GameSettingsDialog):
        GameSettingsDialog.setWindowTitle(QCoreApplication.translate("GameSettingsDialog", u"\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438 \u0438\u0433\u0440\u044b", None))
        self.groupBoardSize.setTitle(QCoreApplication.translate("GameSettingsDialog", u"\u0420\u0430\u0437\u043c\u0435\u0440 \u0434\u043e\u0441\u043a\u0438", None))
        self.radio9x9.setText(QCoreApplication.translate("GameSettingsDialog", u"9x9 (\u043c\u0430\u043b\u0430\u044f)", None))
        self.radio13x13.setText(QCoreApplication.translate("GameSettingsDialog", u"13x13 (\u0441\u0440\u0435\u0434\u043d\u044f\u044f)", None))
        self.radio19x19.setText(QCoreApplication.translate("GameSettingsDialog", u"19x19 (\u0441\u0442\u0430\u043d\u0434\u0430\u0440\u0442\u043d\u0430\u044f)", None))
        self.groupTime.setTitle(QCoreApplication.translate("GameSettingsDialog", u"\u041a\u043e\u043d\u0442\u0440\u043e\u043b\u044c \u0432\u0440\u0435\u043c\u0435\u043d\u0438", None))
        self.labelPlayerTime.setText(QCoreApplication.translate("GameSettingsDialog", u"\u0412\u0440\u0435\u043c\u044f \u043d\u0430 \u0438\u0433\u0440\u043e\u043a\u0430 (\u043c\u0438\u043d\u0443\u0442):", None))
        self.labelByoyomi.setText(QCoreApplication.translate("GameSettingsDialog", u"\u0411\u0451\u0451\u043c\u0438 (\u0441\u0435\u043a\u0443\u043d\u0434):", None))
        self.groupAI.setTitle(QCoreApplication.translate("GameSettingsDialog", u"\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u043f\u043e\u0434\u0441\u043a\u0430\u0437\u043a\u0438", None))
        self.checkLegalMoves.setText(QCoreApplication.translate("GameSettingsDialog", u"\u041f\u043e\u0434\u0441\u0432\u0435\u0447\u0438\u0432\u0430\u0442\u044c \u0434\u043e\u043f\u0443\u0441\u0442\u0438\u043c\u044b\u0435 \u0445\u043e\u0434\u044b", None))
        self.buttonOk.setText(QCoreApplication.translate("GameSettingsDialog", u"\u041d\u0430\u0447\u0430\u0442\u044c \u0438\u0433\u0440\u0443", None))
        self.buttonCancel.setText(QCoreApplication.translate("GameSettingsDialog", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

