import numpy as np
from PyQt5 import QtCore, QtWidgets


class HorizontalHeader(QtWidgets.QHeaderView):
    def __init__(self, values, parent=None):
        super(HorizontalHeader, self).__init__(QtCore.Qt.Horizontal, parent)
        self.setSectionsMovable(True)
        self.values = values
        self.comboboxes = []
        self.sectionResized.connect(self.handleSectionResized)
        self.sectionMoved.connect(self.handleSectionMoved)

    def showEvent(self, event):
        for i in range(self.count()):
            if i < len(self.comboboxes):
                combo = self.comboboxes[i]
                combo.clear()
                combo.addItems(self.values)
            else:
                combo = QtWidgets.QComboBox(self)
                combo.addItems(self.values)
                self.comboboxes.append(combo)

            combo.setGeometry(self.sectionViewportPosition(i), 0, self.sectionSize(i)-4, self.height())
            combo.show()

        if len(self.comboboxes) > self.count():
            for i in range(self.count(), len(self.comboboxes)):
                self.comboboxes[i].deleteLater()

        super(HorizontalHeader, self).showEvent(event)

    def handleSectionResized(self, i):
        for i in range(self.count()):
            j = self.visualIndex(i)
            logical = self.logicalIndex(j)
            self.comboboxes[i].setGeometry(self.sectionViewportPosition(logical), 0, self.sectionSize(logical)-4, self.height())

    def handleSectionMoved(self, i, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            self.comboboxes[i].setGeometry(self.ectionViewportPosition(logical), 0, self.sectionSize(logical) - 5, self.height())

    def fixComboPositions(self):
        for i in range(self.count()):
            self.comboboxes[i].setGeometry(self.sectionViewportPosition(i), 0, self.sectionSize(i) - 5, self.height())

class TableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, header_choices=None):
        super(TableWidget, self).__init__(parent=parent)
        header = HorizontalHeader(values=header_choices, parent=self)
        self.setHorizontalHeader(header)

    def scrollContentsBy(self, dx, dy):
        super(TableWidget, self).scrollContentsBy(dx, dy)
        if dx != 0:
            self.horizontalHeader().fixComboPositions()


class App(QtWidgets.QWidget):
    def __init__(self):
        super(App, self).__init__()
        self.data = np.random.rand(100, 60)
        self.createTable()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)
        self.showMaximized()

    def createTable(self):
        self.header = []
        self.table = TableWidget(self, ["First Name", "Last Name", "Gender", "Age", "Address"])

        self.table.setRowCount(100)
        self.table.setColumnCount(60)

        for i, row_values in enumerate(self.data):
            for j, value in enumerate(row_values):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())