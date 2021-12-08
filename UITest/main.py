import sys

from PyQt5 import QtWidgets
from UITest.UI.LoginWindow import LoginWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ui = LoginWindow()
    # ui_main = TaskWindow.Ui_MainWindow()
    ui.show()

    sys.exit(app.exec_())