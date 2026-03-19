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
from PySide6.QtWidgets import (QApplication, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QWidget)

from core.go_board_widget import GoBoardWidget

class Ui_main(object):
    def setupUi(self, main):
        if not main.objectName():
            main.setObjectName(u"main")
        main.resize(752, 543)
        self.boardWidget = GoBoardWidget(main)
        self.boardWidget.setObjectName(u"boardWidget")
        self.boardWidget.setGeometry(QRect(40, 30, 421, 421))
        self.playerAvatar = QPushButton(main)
        self.playerAvatar.setObjectName(u"playerAvatar")
        self.playerAvatar.setGeometry(QRect(480, 390, 54, 54))
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
        self.opponentAvatar = QPushButton(main)
        self.opponentAvatar.setObjectName(u"opponentAvatar")
        self.opponentAvatar.setGeometry(QRect(480, 30, 54, 54))
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
        self.playerName = QLabel(main)
        self.playerName.setObjectName(u"playerName")
        self.playerName.setGeometry(QRect(540, 400, 81, 31))
        self.opponentName = QLabel(main)
        self.opponentName.setObjectName(u"opponentName")
        self.opponentName.setGeometry(QRect(540, 40, 81, 31))
        self.timer = QLabel(main)
        self.timer.setObjectName(u"timer")
        self.timer.setGeometry(QRect(660, 120, 81, 31))
        self.buttonPass = QPushButton(main)
        self.buttonPass.setObjectName(u"buttonPass")
        self.buttonPass.setGeometry(QRect(640, 220, 101, 31))
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
        self.buttonResign = QPushButton(main)
        self.buttonResign.setObjectName(u"buttonResign")
        self.buttonResign.setGeometry(QRect(640, 280, 101, 31))
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
        self.buttonChat = QPushButton(main)
        self.buttonChat.setObjectName(u"buttonChat")
        self.buttonChat.setGeometry(QRect(500, 270, 101, 41))
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
        self.capturedBTplayer = QLabel(main)
        self.capturedBTplayer.setObjectName(u"capturedBTplayer")
        self.capturedBTplayer.setGeometry(QRect(660, 400, 51, 31))
        self.capturedBToppnent = QLabel(main)
        self.capturedBToppnent.setObjectName(u"capturedBToppnent")
        self.capturedBToppnent.setGeometry(QRect(660, 40, 51, 31))
        self.buttonPrevMove = QPushButton(main)
        self.buttonPrevMove.setObjectName(u"buttonPrevMove")
        self.buttonPrevMove.setGeometry(QRect(40, 460, 201, 31))
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
        self.buttonNextMove = QPushButton(main)
        self.buttonNextMove.setObjectName(u"buttonNextMove")
        self.buttonNextMove.setGeometry(QRect(260, 460, 201, 31))
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
        self.historyList = QListWidget(main)
        self.historyList.setObjectName(u"historyList")
        self.historyList.setGeometry(QRect(40, 500, 421, 31))
        self.historyList.setStyleSheet(u"")

        self.retranslateUi(main)

        QMetaObject.connectSlotsByName(main)
    # setupUi

    def retranslateUi(self, main):
        main.setWindowTitle(QCoreApplication.translate("main", u"Form", None))
        self.playerAvatar.setText(QCoreApplication.translate("main", u"playerAvatar", None))
        self.opponentAvatar.setText(QCoreApplication.translate("main", u"opponentAvatar", None))
        self.playerName.setText(QCoreApplication.translate("main", u"playerName", None))
        self.opponentName.setText(QCoreApplication.translate("main", u"opponentName", None))
        self.timer.setText(QCoreApplication.translate("main", u"timer", None))
        self.buttonPass.setText(QCoreApplication.translate("main", u"Pass", None))
        self.buttonResign.setText(QCoreApplication.translate("main", u"Resign", None))
        self.buttonChat.setText(QCoreApplication.translate("main", u"Chat", None))
        self.capturedBTplayer.setText(QCoreApplication.translate("main", u"capPlayer", None))
        self.capturedBToppnent.setText(QCoreApplication.translate("main", u"capOppnent", None))
        self.buttonPrevMove.setText(QCoreApplication.translate("main", u"PrevMove", None))
        self.buttonNextMove.setText(QCoreApplication.translate("main", u"NextMove", None))
    # retranslateUi

