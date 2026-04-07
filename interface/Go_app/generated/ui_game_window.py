# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_window.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from core.go_board_widget import GoBoardWidget

class Ui_main(object):
    def setupUi(self, main):
        if not main.objectName():
            main.setObjectName(u"main")
        main.resize(1059, 785)
        self.layoutWidget1 = QWidget(main)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(260, 640, 501, 61))
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.playerAvatar = QPushButton(self.layoutWidget1)
        self.playerAvatar.setObjectName(u"playerAvatar")
        self.playerAvatar.setStyleSheet(u"QPushButton#playerAvatar {\n"
"    border: 2px solid #4CAF50;           /* \u0437\u0435\u043b\u0435\u043d\u0430\u044f \u0440\u0430\u043c\u043a\u0430 */\n"
"    border-radius: 25px;                  /* \u043f\u043e\u043b\u043e\u0432\u0438\u043d\u0430 \u043e\u0442 \u0448\u0438\u0440\u0438\u043d\u044b/\u0432\u044b\u0441\u043e\u0442\u044b */\n"
"    background-color: transparent;        /* \u043f\u0440\u043e\u0437\u0440\u0430\u0447\u043d\u044b\u0439 \u0444\u043e\u043d */\n"
"    min-width: 50px;                      /* \u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u0440\u0430\u0437\u043c\u0435\u0440 */\n"
"    min-height: 50px;\n"
"    max-width: 50px;\n"
"    max-height: 50px;\n"
"}\n"
"\n"
"/* \u042d\u0444\u0444\u0435\u043a\u0442 \u043f\u0440\u0438 \u043d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0438 */\n"
"QPushButton#playerAvatar:hover{\n"
"    border-color: #FF9800;                 /* \u043e\u0440\u0430\u043d\u0436\u0435\u0432\u0430\u044f \u0440\u0430\u043c\u043a\u0430 \u043f"
                        "\u0440\u0438 \u043d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0438 */\n"
"    opacity: 0.8;\n"
"}")

        self.horizontalLayout_2.addWidget(self.playerAvatar)

        self.playerName = QLabel(self.layoutWidget1)
        self.playerName.setObjectName(u"playerName")

        self.horizontalLayout_2.addWidget(self.playerName)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.timerPlayer = QLabel(self.layoutWidget1)
        self.timerPlayer.setObjectName(u"timerPlayer")

        self.horizontalLayout_2.addWidget(self.timerPlayer)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.capturedBTplayer = QLabel(self.layoutWidget1)
        self.capturedBTplayer.setObjectName(u"capturedBTplayer")

        self.horizontalLayout_2.addWidget(self.capturedBTplayer)

        self.horizontalLayout_2.setStretch(0, 2)
        self.horizontalLayout_2.setStretch(1, 3)
        self.horizontalLayout_2.setStretch(2, 7)
        self.horizontalLayout_2.setStretch(3, 1)
        self.horizontalLayout_2.setStretch(4, 5)
        self.horizontalLayout_2.setStretch(5, 1)
        self.layoutWidget2 = QWidget(main)
        self.layoutWidget2.setObjectName(u"layoutWidget2")
        self.layoutWidget2.setGeometry(QRect(270, 80, 491, 56))
        self.horizontalLayout = QHBoxLayout(self.layoutWidget2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.opponentAvatar = QPushButton(self.layoutWidget2)
        self.opponentAvatar.setObjectName(u"opponentAvatar")
        self.opponentAvatar.setStyleSheet(u"QPushButton#opponentAvatar {\n"
"    border: 2px solid #4CAF50;           /* \u0437\u0435\u043b\u0435\u043d\u0430\u044f \u0440\u0430\u043c\u043a\u0430 */\n"
"    border-radius: 25px;                  /* \u043f\u043e\u043b\u043e\u0432\u0438\u043d\u0430 \u043e\u0442 \u0448\u0438\u0440\u0438\u043d\u044b/\u0432\u044b\u0441\u043e\u0442\u044b */\n"
"    background-color: transparent;        /* \u043f\u0440\u043e\u0437\u0440\u0430\u0447\u043d\u044b\u0439 \u0444\u043e\u043d */\n"
"    min-width: 50px;                      /* \u0444\u0438\u043a\u0441\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u0440\u0430\u0437\u043c\u0435\u0440 */\n"
"    min-height: 50px;\n"
"    max-width: 50px;\n"
"    max-height: 50px;\n"
"}\n"
"\n"
"/* \u042d\u0444\u0444\u0435\u043a\u0442 \u043f\u0440\u0438 \u043d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0438 */\n"
"QPushButton#opponentAvatar:hover{\n"
"    border-color: #FF9800;                 /* \u043e\u0440\u0430\u043d\u0436\u0435\u0432\u0430\u044f \u0440\u0430\u043c\u043a\u0430 "
                        "\u043f\u0440\u0438 \u043d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0438 */\n"
"    opacity: 0.8;\n"
"}")

        self.horizontalLayout.addWidget(self.opponentAvatar)

        self.opponentName = QLabel(self.layoutWidget2)
        self.opponentName.setObjectName(u"opponentName")

        self.horizontalLayout.addWidget(self.opponentName)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.timerOpponent = QLabel(self.layoutWidget2)
        self.timerOpponent.setObjectName(u"timerOpponent")

        self.horizontalLayout.addWidget(self.timerOpponent)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.capturedBToppnent = QLabel(self.layoutWidget2)
        self.capturedBToppnent.setObjectName(u"capturedBToppnent")

        self.horizontalLayout.addWidget(self.capturedBToppnent)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 3)
        self.horizontalLayout.setStretch(2, 7)
        self.horizontalLayout.setStretch(3, 1)
        self.horizontalLayout.setStretch(4, 5)
        self.horizontalLayout.setStretch(5, 1)
        self.layoutWidget3 = QWidget(main)
        self.layoutWidget3.setObjectName(u"layoutWidget3")
        self.layoutWidget3.setGeometry(QRect(810, 660, 251, 41))
        self.horizontalLayout_3 = QHBoxLayout(self.layoutWidget3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.buttonResign = QPushButton(self.layoutWidget3)
        self.buttonResign.setObjectName(u"buttonResign")
        self.buttonResign.setStyleSheet(u"QPushButton#buttonResign {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 5px;\n"
"    color: white;\n"
"    padding: 5px 15px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonResign:hover {\n"
"    opacity: 0.9;\n"
"    filter: brightness(110%);\n"
"}")

        self.horizontalLayout_3.addWidget(self.buttonResign)

        self.buttonPass = QPushButton(self.layoutWidget3)
        self.buttonPass.setObjectName(u"buttonPass")
        self.buttonPass.setStyleSheet(u"QPushButton#buttonPass {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 5px;\n"
"    color: white;\n"
"    padding: 5px 15px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonPass:hover {\n"
"    opacity: 0.9;\n"
"    filter: brightness(110%);\n"
"}")

        self.horizontalLayout_3.addWidget(self.buttonPass)

        self.layoutWidget = QWidget(main)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(0, 140, 1061, 501))
        self.horizontalLayout_7 = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.buttonChat = QPushButton(self.layoutWidget)
        self.buttonChat.setObjectName(u"buttonChat")
        self.buttonChat.setStyleSheet(u"QPushButton#buttonChat {\n"
"    background-color: #2196F3;\n"
"    border-radius: 5px;\n"
"    color: white;\n"
"    padding: 8px 15px;\n"
"    font-size: 14px;\n"
"}\n"
"QPushButton#buttonChat:hover {\n"
"    opacity: 0.9;\n"
"    filter: brightness(110%);\n"
"}")

        self.horizontalLayout_6.addWidget(self.buttonChat)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_5)

        self.boardWidget = GoBoardWidget(self.layoutWidget)
        self.boardWidget.setObjectName(u"boardWidget")

        self.horizontalLayout_6.addWidget(self.boardWidget)

        self.horizontalLayout_6.setStretch(0, 8)
        self.horizontalLayout_6.setStretch(1, 1)
        self.horizontalLayout_6.setStretch(2, 18)

        self.horizontalLayout_7.addLayout(self.horizontalLayout_6)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_6)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.historyList = QListWidget(self.layoutWidget)
        self.historyList.setObjectName(u"historyList")
        self.historyList.setStyleSheet(u"")

        self.verticalLayout.addWidget(self.historyList)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.buttonPrevMove = QPushButton(self.layoutWidget)
        self.buttonPrevMove.setObjectName(u"buttonPrevMove")
        self.buttonPrevMove.setStyleSheet(u"QPushButton#buttonPrevMove {\n"
"    background-color: #FF9800;\n"
"    border-radius: 5px;\n"
"    color: white;\n"
"    padding: 5px 20px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonPrevMove:hover {\n"
"    opacity: 0.9;\n"
"    filter: brightness(110%);\n"
"}")

        self.horizontalLayout_4.addWidget(self.buttonPrevMove)

        self.buttonNextMove = QPushButton(self.layoutWidget)
        self.buttonNextMove.setObjectName(u"buttonNextMove")
        self.buttonNextMove.setStyleSheet(u"QPushButton#buttonNextMove {\n"
"    background-color: #FF9800;\n"
"    border-radius: 5px;\n"
"    color: white;\n"
"    padding: 5px 20px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonNextMove:hover {\n"
"    opacity: 0.9;\n"
"    filter: brightness(110%);\n"
"}")

        self.horizontalLayout_4.addWidget(self.buttonNextMove)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.verticalLayout.setStretch(0, 10)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 2)
        self.verticalLayout.setStretch(3, 1)

        self.horizontalLayout_5.addLayout(self.verticalLayout)

        self.horizontalLayout_5.setStretch(0, 7)

        self.horizontalLayout_7.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_7.setStretch(0, 24)
        self.horizontalLayout_7.setStretch(1, 1)
        self.horizontalLayout_7.setStretch(2, 8)

        self.retranslateUi(main)

        QMetaObject.connectSlotsByName(main)
    # setupUi

    def retranslateUi(self, main):
        main.setWindowTitle(QCoreApplication.translate("main", u"Form", None))
        self.playerAvatar.setText(QCoreApplication.translate("main", u"playerAvatar", None))
        self.playerName.setText(QCoreApplication.translate("main", u"playerName", None))
        self.timerPlayer.setText(QCoreApplication.translate("main", u"PlayerTimer", None))
        self.capturedBTplayer.setText(QCoreApplication.translate("main", u"capPlayer", None))
        self.opponentAvatar.setText(QCoreApplication.translate("main", u"opponentAvatar", None))
        self.opponentName.setText(QCoreApplication.translate("main", u"opponentName", None))
        self.timerOpponent.setText(QCoreApplication.translate("main", u"OpponentTimer", None))
        self.capturedBToppnent.setText(QCoreApplication.translate("main", u"capOppnent", None))
        self.buttonResign.setText(QCoreApplication.translate("main", u"Resign", None))
        self.buttonPass.setText(QCoreApplication.translate("main", u"Pass", None))
        self.buttonChat.setText(QCoreApplication.translate("main", u"Chat", None))
        self.buttonPrevMove.setText(QCoreApplication.translate("main", u"PrevMove", None))
        self.buttonNextMove.setText(QCoreApplication.translate("main", u"NextMove", None))
    # retranslateUi

