# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_windowPvP.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from core.go_board_widget import GoBoardWidget

class Ui_main(object):
    def setupUi(self, main):
        if not main.objectName():
            main.setObjectName(u"main")
        main.resize(1108, 781)
        self.horizontalLayout_11 = QHBoxLayout(main)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_3)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_7)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.opponentAvatar = QPushButton(main)
        self.opponentAvatar.setObjectName(u"opponentAvatar")
        self.opponentAvatar.setStyleSheet(u"QPushButton#opponentAvatar {\n"
"    border-radius: 25px;\n"
"    min-width: 50px;\n"
"    min-height: 50px;\n"
"    max-width: 50px;\n"
"    max-height: 50px;\n"
"}\n"
"QPushButton#opponentAvatar:hover {\n"
"    opacity: 0.8;\n"
"}")

        self.horizontalLayout.addWidget(self.opponentAvatar)

        self.opponentName = QLabel(main)
        self.opponentName.setObjectName(u"opponentName")

        self.horizontalLayout.addWidget(self.opponentName)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.timerOpponent = QLabel(main)
        self.timerOpponent.setObjectName(u"timerOpponent")

        self.horizontalLayout.addWidget(self.timerOpponent)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.capturedBToppnent = QLabel(main)
        self.capturedBToppnent.setObjectName(u"capturedBToppnent")

        self.horizontalLayout.addWidget(self.capturedBToppnent)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 3)
        self.horizontalLayout.setStretch(2, 7)
        self.horizontalLayout.setStretch(3, 1)
        self.horizontalLayout.setStretch(4, 5)
        self.horizontalLayout.setStretch(5, 1)

        self.horizontalLayout_8.addLayout(self.horizontalLayout)

        self.horizontalSpacer_8 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_8)

        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 11)
        self.horizontalLayout_8.setStretch(2, 12)

        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_11)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.boardWidget = GoBoardWidget(main)
        self.boardWidget.setObjectName(u"boardWidget")

        self.horizontalLayout_6.addWidget(self.boardWidget)

        self.horizontalLayout_6.setStretch(0, 18)

        self.horizontalLayout_7.addLayout(self.horizontalLayout_6)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_6)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.historyList = QListWidget(main)
        self.historyList.setObjectName(u"historyList")
        self.historyList.setStyleSheet(u"")

        self.verticalLayout.addWidget(self.historyList)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.buttonPrevMove = QPushButton(main)
        self.buttonPrevMove.setObjectName(u"buttonPrevMove")
        self.buttonPrevMove.setStyleSheet(u"QPushButton#buttonPrevMove {\n"
"    border-radius: 5px;\n"
"    padding: 5px 20px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonPrevMove:hover {\n"
"    opacity: 0.9;\n"
"}")

        self.horizontalLayout_4.addWidget(self.buttonPrevMove)

        self.buttonNextMove = QPushButton(main)
        self.buttonNextMove.setObjectName(u"buttonNextMove")
        self.buttonNextMove.setStyleSheet(u"QPushButton#buttonNextMove {\n"
"    border-radius: 5px;\n"
"    padding: 5px 20px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonNextMove:hover {\n"
"    opacity: 0.9;\n"
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

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_5)

        self.horizontalLayout_7.setStretch(1, 3)
        self.horizontalLayout_7.setStretch(2, 1)
        self.horizontalLayout_7.setStretch(3, 2)

        self.verticalLayout_2.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_9)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.playerAvatar = QPushButton(main)
        self.playerAvatar.setObjectName(u"playerAvatar")
        self.playerAvatar.setStyleSheet(u"QPushButton#playerAvatar {\n"
"    border-radius: 25px;\n"
"    min-width: 50px;\n"
"    min-height: 50px;\n"
"    max-width: 50px;\n"
"    max-height: 50px;\n"
"}\n"
"QPushButton#playerAvatar:hover {\n"
"    opacity: 0.8;\n"
"}")

        self.horizontalLayout_2.addWidget(self.playerAvatar)

        self.playerName = QLabel(main)
        self.playerName.setObjectName(u"playerName")

        self.horizontalLayout_2.addWidget(self.playerName)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.timerPlayer = QLabel(main)
        self.timerPlayer.setObjectName(u"timerPlayer")

        self.horizontalLayout_2.addWidget(self.timerPlayer)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_4)

        self.capturedBTplayer = QLabel(main)
        self.capturedBTplayer.setObjectName(u"capturedBTplayer")

        self.horizontalLayout_2.addWidget(self.capturedBTplayer)

        self.horizontalLayout_2.setStretch(0, 2)
        self.horizontalLayout_2.setStretch(1, 3)
        self.horizontalLayout_2.setStretch(2, 7)
        self.horizontalLayout_2.setStretch(3, 1)
        self.horizontalLayout_2.setStretch(4, 5)
        self.horizontalLayout_2.setStretch(5, 1)

        self.horizontalLayout_10.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_9.addItem(self.horizontalSpacer_10)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.buttonResign = QPushButton(main)
        self.buttonResign.setObjectName(u"buttonResign")
        self.buttonResign.setStyleSheet(u"QPushButton#buttonResign {\n"
"    border-radius: 5px;\n"
"    padding: 5px 15px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonResign:hover {\n"
"    opacity: 0.9;\n"
"}")

        self.horizontalLayout_3.addWidget(self.buttonResign)

        self.buttonPass = QPushButton(main)
        self.buttonPass.setObjectName(u"buttonPass")
        self.buttonPass.setStyleSheet(u"QPushButton#buttonPass {\n"
"    border-radius: 5px;\n"
"    padding: 5px 15px;\n"
"    font-size: 12px;\n"
"}\n"
"QPushButton#buttonPass:hover {\n"
"    opacity: 0.9;\n"
"}")

        self.horizontalLayout_3.addWidget(self.buttonPass)

        self.horizontalSpacer_12 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_12)

        self.horizontalLayout_3.setStretch(0, 2)
        self.horizontalLayout_3.setStretch(1, 2)

        self.horizontalLayout_9.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_9.setStretch(0, 5)
        self.horizontalLayout_9.setStretch(1, 12)

        self.horizontalLayout_10.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_10.setStretch(0, 1)
        self.horizontalLayout_10.setStretch(1, 11)
        self.horizontalLayout_10.setStretch(2, 12)

        self.verticalLayout_2.addLayout(self.horizontalLayout_10)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_4)

        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 2)
        self.verticalLayout_2.setStretch(2, 12)
        self.verticalLayout_2.setStretch(3, 2)
        self.verticalLayout_2.setStretch(4, 1)

        self.horizontalLayout_11.addLayout(self.verticalLayout_2)


        self.retranslateUi(main)

        QMetaObject.connectSlotsByName(main)
    # setupUi

    def retranslateUi(self, main):
        main.setWindowTitle(QCoreApplication.translate("main", u"Form", None))
        self.opponentAvatar.setText(QCoreApplication.translate("main", u"opponentAvatar", None))
        self.opponentName.setText(QCoreApplication.translate("main", u"opponentName", None))
        self.timerOpponent.setText(QCoreApplication.translate("main", u"OpponentTimer", None))
        self.capturedBToppnent.setText(QCoreApplication.translate("main", u"capOppnent", None))
        self.buttonPrevMove.setText(QCoreApplication.translate("main", u"PrevMove", None))
        self.buttonNextMove.setText(QCoreApplication.translate("main", u"NextMove", None))
        self.playerAvatar.setText(QCoreApplication.translate("main", u"playerAvatar", None))
        self.playerName.setText(QCoreApplication.translate("main", u"playerName", None))
        self.timerPlayer.setText(QCoreApplication.translate("main", u"PlayerTimer", None))
        self.capturedBTplayer.setText(QCoreApplication.translate("main", u"capPlayer", None))
        self.buttonResign.setText(QCoreApplication.translate("main", u"Resign", None))
        self.buttonPass.setText(QCoreApplication.translate("main", u"Pass", None))
    # retranslateUi

