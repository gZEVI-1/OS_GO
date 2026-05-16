# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rules_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QPushButton,
    QSizePolicy, QSpacerItem, QTextBrowser, QVBoxLayout,
    QWidget)

class Ui_RulesDialog(object):
    def setupUi(self, RulesDialog):
        if not RulesDialog.objectName():
            RulesDialog.setObjectName(u"RulesDialog")
        RulesDialog.resize(700, 600)
        self.verticalLayout = QVBoxLayout(RulesDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.textBrowser = QTextBrowser(RulesDialog)
        self.textBrowser.setObjectName(u"textBrowser")
        self.textBrowser.setOpenExternalLinks(False)

        self.verticalLayout.addWidget(self.textBrowser)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.buttonClose = QPushButton(RulesDialog)
        self.buttonClose.setObjectName(u"buttonClose")
        self.buttonClose.setFixedWidth(120)

        self.horizontalLayout.addWidget(self.buttonClose)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(RulesDialog)

        QMetaObject.connectSlotsByName(RulesDialog)
    # setupUi

    def retranslateUi(self, RulesDialog):
        RulesDialog.setWindowTitle(QCoreApplication.translate("RulesDialog", u"Rules", None))
        self.buttonClose.setText(QCoreApplication.translate("RulesDialog", u"Close", None))
    # retranslateUi

