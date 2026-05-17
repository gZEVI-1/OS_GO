# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_profile.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_ProfileWindow(object):
    def setupUi(self, ProfileWindow):
        if not ProfileWindow.objectName():
            ProfileWindow.setObjectName(u"ProfileWindow")
        ProfileWindow.resize(450, 500)
        self.verticalLayout = QVBoxLayout(ProfileWindow)
        self.verticalLayout.setSpacing(15)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.topLayout = QHBoxLayout()
        self.topLayout.setObjectName(u"topLayout")
        self.leftSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.topLayout.addItem(self.leftSpacer)

        self.avatarContainerLayout = QVBoxLayout()
        self.avatarContainerLayout.setObjectName(u"avatarContainerLayout")
        self.avatarButton = QPushButton(ProfileWindow)
        self.avatarButton.setObjectName(u"avatarButton")
        self.avatarButton.setMinimumSize(QSize(120, 120))
        self.avatarButton.setMaximumSize(QSize(120, 120))
        self.avatarButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.avatarButton.setStyleSheet(u"\n"
"           QPushButton {\n"
"               border-radius: 60px;\n"
"           }\n"
"          ")
        self.avatarButton.setIconSize(QSize(120, 120))

        self.avatarContainerLayout.addWidget(self.avatarButton)


        self.topLayout.addLayout(self.avatarContainerLayout)

        self.rightSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.topLayout.addItem(self.rightSpacer)


        self.verticalLayout.addLayout(self.topLayout)

        self.emailLayout = QHBoxLayout()
        self.emailLayout.setObjectName(u"emailLayout")
        self.emailLabel = QLabel(ProfileWindow)
        self.emailLabel.setObjectName(u"emailLabel")
        self.emailLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.emailLayout.addWidget(self.emailLabel)


        self.verticalLayout.addLayout(self.emailLayout)

        self.middleSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.middleSpacer)

        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setObjectName(u"buttonsLayout")
        self.statsButton = QPushButton(ProfileWindow)
        self.statsButton.setObjectName(u"statsButton")
        self.statsButton.setMinimumSize(QSize(220, 45))
        self.statsButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.statsButton.setStyleSheet(u"\n"
"         QPushButton {\n"
"             border-radius: 10px;\n"
"         }\n"
"        ")

        self.buttonsLayout.addWidget(self.statsButton)


        self.verticalLayout.addLayout(self.buttonsLayout)

        self.editLayout = QHBoxLayout()
        self.editLayout.setObjectName(u"editLayout")
        self.editProfileButton = QPushButton(ProfileWindow)
        self.editProfileButton.setObjectName(u"editProfileButton")
        self.editProfileButton.setMinimumSize(QSize(220, 45))
        self.editProfileButton.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.editProfileButton.setStyleSheet(u"\n"
"         QPushButton {\n"
"             border-radius: 10px;\n"
"         }\n"
"        ")

        self.editLayout.addWidget(self.editProfileButton)


        self.verticalLayout.addLayout(self.editLayout)

        self.bottomSpacer = QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.bottomSpacer)

        self.buttonBoxLayout = QHBoxLayout()
        self.buttonBoxLayout.setObjectName(u"buttonBoxLayout")
        self.buttonBox = QDialogButtonBox(ProfileWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStyleSheet(u"\n"
"         QPushButton {\n"
"             border-radius: 8px;\n"
"         }\n"
"        ")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        self.buttonBox.setCenterButtons(True)

        self.buttonBoxLayout.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.buttonBoxLayout)


        self.retranslateUi(ProfileWindow)
        self.buttonBox.rejected.connect(ProfileWindow.reject)

        QMetaObject.connectSlotsByName(ProfileWindow)
    # setupUi

    def retranslateUi(self, ProfileWindow):
        ProfileWindow.setWindowTitle(QCoreApplication.translate("ProfileWindow", u"\u041f\u0440\u043e\u0444\u0438\u043b\u044c", None))
        self.avatarButton.setText("")
        self.emailLabel.setText(QCoreApplication.translate("ProfileWindow", u"email@example.com", None))
        self.statsButton.setText(QCoreApplication.translate("ProfileWindow", u" \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430 \u0430\u043a\u043a\u0430\u0443\u043d\u0442\u0430", None))
        self.editProfileButton.setText(QCoreApplication.translate("ProfileWindow", u" \u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043f\u0440\u043e\u0444\u0438\u043b\u044c", None))
    # retranslateUi

