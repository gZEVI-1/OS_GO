# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
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
from PySide6.QtWidgets import (QApplication, QDockWidget, QHBoxLayout, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_mainWindow(object):
    def setupUi(self, mainWindow):
        if not mainWindow.objectName():
            mainWindow.setObjectName(u"mainWindow")
        mainWindow.resize(1059, 785)
        self.verticalLayout_4 = QVBoxLayout(mainWindow)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.sidebar = QDockWidget(mainWindow)
        self.sidebar.setObjectName(u"sidebar")
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_3 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.buttonAccount = QPushButton(self.dockWidgetContents)
        self.buttonAccount.setObjectName(u"buttonAccount")
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

        self.verticalLayout_3.addWidget(self.buttonAccount)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_3)

        self.buttonSettings = QPushButton(self.dockWidgetContents)
        self.buttonSettings.setObjectName(u"buttonSettings")
        self.buttonSettings.setStyleSheet(u"QPushButton {\n"
"    border: none;\n"
"    background-color: transparent;\n"
"}")
        icon = QIcon()
        icon.addFile(u"C:/Users/polin/Downloads/pngegg.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.buttonSettings.setIcon(icon)
        self.buttonSettings.setIconSize(QSize(30, 30))

        self.verticalLayout_3.addWidget(self.buttonSettings)

        self.sidebar.setWidget(self.dockWidgetContents)

        self.horizontalLayout_3.addWidget(self.sidebar)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(15)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.buttonWindOnline = QPushButton(mainWindow)
        self.buttonWindOnline.setObjectName(u"buttonWindOnline")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonWindOnline.sizePolicy().hasHeightForWidth())
        self.buttonWindOnline.setSizePolicy(sizePolicy)
        self.buttonWindOnline.setStyleSheet(u"QPushButton#buttonWindOnline {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"}")

        self.horizontalLayout.addWidget(self.buttonWindOnline)

        self.buttonWindOffline = QPushButton(mainWindow)
        self.buttonWindOffline.setObjectName(u"buttonWindOffline")
        sizePolicy.setHeightForWidth(self.buttonWindOffline.sizePolicy().hasHeightForWidth())
        self.buttonWindOffline.setSizePolicy(sizePolicy)
        self.buttonWindOffline.setStyleSheet(u"QPushButton#buttonWindOffline{\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"}")

        self.horizontalLayout.addWidget(self.buttonWindOffline)

        self.buttonWindBot = QPushButton(mainWindow)
        self.buttonWindBot.setObjectName(u"buttonWindBot")
        sizePolicy.setHeightForWidth(self.buttonWindBot.sizePolicy().hasHeightForWidth())
        self.buttonWindBot.setSizePolicy(sizePolicy)
        self.buttonWindBot.setStyleSheet(u"QPushButton#buttonWindBot {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 10px;  \n"
"    color: white;\n"
"    padding: 8px 16px;\n"
"}")

        self.horizontalLayout.addWidget(self.buttonWindBot)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.buttonInstruct = QPushButton(mainWindow)
        self.buttonInstruct.setObjectName(u"buttonInstruct")
        sizePolicy.setHeightForWidth(self.buttonInstruct.sizePolicy().hasHeightForWidth())
        self.buttonInstruct.setSizePolicy(sizePolicy)
        self.buttonInstruct.setStyleSheet(u"QPushButton#buttonInstruct {\n"
"    background-color: #4CAF50;\n"
"    border-radius: 2.5px;\n"
"    color: white;\n"
"    border: 1px solid #388E3C;\n"
"}")

        self.horizontalLayout_2.addWidget(self.buttonInstruct)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 3)
        self.horizontalLayout_2.setStretch(2, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalLayout.setStretch(0, 4)
        self.verticalLayout.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 2)
        self.verticalLayout_2.setStretch(2, 1)

        self.horizontalLayout_3.addLayout(self.verticalLayout_2)

        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 14)

        self.verticalLayout_4.addLayout(self.horizontalLayout_3)


        self.retranslateUi(mainWindow)

        QMetaObject.connectSlotsByName(mainWindow)
    # setupUi

    def retranslateUi(self, mainWindow):
        mainWindow.setWindowTitle(QCoreApplication.translate("mainWindow", u"Widget", None))
        self.buttonAccount.setText(QCoreApplication.translate("mainWindow", u"account", None))
        self.buttonWindOnline.setText(QCoreApplication.translate("mainWindow", u"openOnline", None))
        self.buttonWindOffline.setText(QCoreApplication.translate("mainWindow", u"openOffline", None))
        self.buttonWindBot.setText(QCoreApplication.translate("mainWindow", u"openBot", None))
        self.buttonInstruct.setText(QCoreApplication.translate("mainWindow", u"openInstruct", None))
    # retranslateUi

