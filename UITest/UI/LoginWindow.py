# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'LoginWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
import sys

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QMessageBox

from UITest.UI import TaskWindow, Config
from UITest.encrypt import Coder
from UITest.utils.Tool import get_mac_address
from UITest.Usr import User


ui_main = None

class LoginWindow(QMainWindow):

    def __init__(self):
        super(LoginWindow, self).__init__()

        self.deviceId = get_mac_address()
        Config.Device_Mac = self.deviceId
        print("Mac地址: " + self.deviceId)

        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.horizontalLayout_2.addWidget(self.lineEdit_2)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "登陆"))
        self.label.setText(_translate("MainWindow", "用户名："))
        self.label_2.setText(_translate("MainWindow", "密   码："))
        self.pushButton.setText(_translate("MainWindow", "登陆"))

        self.pushButton.clicked.connect(self.on_login)

    def show_main(self):
        LoginWindow.ui_main = TaskWindow.Ui_MainWindow()
        LoginWindow.ui_main.show()
        self.close()

    def on_login(self):

        url = 'https://www.yimao1.com/api/login'
        import requests

        account = self.lineEdit.text()
        if account is None or len(account) == 0:
            self.alert_msg("请输入账号")
            return

        password = self.lineEdit_2.text()
        if password is None or len(password) == 0:
            self.alert_msg("请输入密码")
            return

        password = Coder.encrpt(password)
        identifier = Coder.encrpt(self.deviceId)

        post_data = {
            "account": account,
            "password": password,
            "identifier": identifier,
        }

        try:
            res = requests.post(url=url, data=post_data)
            if res.status_code == 200:
                js = res.json()
                code = js.get('code', None)

                if code is not None and code == 0:
                    # self.alert_msg("登陆成功")

                    data = js.get('data', None)
                    if data is None:
                        QMessageBox.about(self, '温馨提示', "未知错误")
                        return
                    expire_date = data.get('expire_date', 0)
                    if expire_date <= 0:
                        QMessageBox.about(self, '温馨提示', "账号已过期")
                        return

                    User.User_Account = account
                    User.User_Mac = identifier
                    User.User_Expire = expire_date

                    self.show_main()
                else:
                    msg = js.get("msg", "未知错误")
                    self.alert_msg(msg)
            else:
                QMessageBox.about(self, '温馨提示', "网络错误……")
        except:
            QMessageBox.about(self, '温馨提示', "网络错误……")

    def alert_msg(self, msg):
        QMessageBox.about(self, '温馨提示', msg)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ui = LoginWindow()
    # ui_main = TaskWindow.Ui_MainWindow()
    ui.show()

    sys.exit(app.exec_())