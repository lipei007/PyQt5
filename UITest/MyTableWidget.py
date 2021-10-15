from typing import Iterable

from PyQt5 import QtCore, QtWidgets


class HorizontalHeader(QtWidgets.QHeaderView):
    def __init__(self, parent=None, values=None):
        super(HorizontalHeader, self).__init__(QtCore.Qt.Horizontal, parent)
        self.setSectionsMovable(True)
        self.values = values
        self.comboboxes = []
        self.sectionResized.connect(self.handleSectionResized)
        self.sectionMoved.connect(self.handleSectionMoved)

    def set_choices(self, values):
        self.values = values

    def header_values(self):
        dic0 = dict()
        for i, combo in enumerate(self.comboboxes):
            dic0[i] = combo.currentText()

        return dic0

    def on_changed(self):
        if len(self.comboboxes) == self.count():
            return
        for i in range(self.count()):
            if i < len(self.comboboxes):
                combo = self.comboboxes[i]
                combo.clear()
                combo.addItems(self.values)
            else:
                combo = QtWidgets.QComboBox(self)
                combo.addItems(self.values)
                self.comboboxes.append(combo)

            combo.setGeometry(self.sectionViewportPosition(i), 0, self.sectionSize(i) - 4, self.height())
            combo.show()

        if len(self.comboboxes) > self.count():
            for i in range(self.count(), len(self.comboboxes)):
                self.comboboxes[i].deleteLater()

    def dataChanged(self, QModelIndex, QModelIndex_1, roles: Iterable[int] = []):
        super(HorizontalHeader, self).dataChanged(QModelIndex, QModelIndex_1, roles)
        self.on_changed()

    def headerDataChanged(self, Qt_Orientation, p_int, p_int_1):
        super(HorizontalHeader, self).headerDataChanged(Qt_Orientation, p_int, p_int_1)
        self.on_changed()

    def showEvent(self, event):
        self.on_changed()

        super(HorizontalHeader, self).showEvent(event)

    def handleSectionResized(self, i):
        for i in range(self.count()):
            j = self.visualIndex(i)
            logical = self.logicalIndex(j)
            self.comboboxes[i].setGeometry(self.sectionViewportPosition(logical), 0, self.sectionSize(logical) - 4,
                                           self.height())

    def handleSectionMoved(self, i, oldVisualIndex, newVisualIndex):
        for i in range(min(oldVisualIndex, newVisualIndex), self.count()):
            logical = self.logicalIndex(i)
            self.comboboxes[i].setGeometry(self.ectionViewportPosition(logical), 0, self.sectionSize(logical) - 5,
                                           self.height())

    def fixComboPositions(self):
        for i in range(self.count()):
            self.comboboxes[i].setGeometry(self.sectionViewportPosition(i), 0, self.sectionSize(i) - 5, self.height())


class MyTableWidget(QtWidgets.QTableWidget):
    def __init__(self, parent=None, header_choices=None):
        super(MyTableWidget, self).__init__(parent=parent)
        self.h_header = HorizontalHeader(parent=self, values=header_choices)
        self.setHorizontalHeader(self.h_header)

    def scrollContentsBy(self, dx, dy):
        super(MyTableWidget, self).scrollContentsBy(dx, dy)
        if dx != 0:
            self.horizontalHeader().fixComboPositions()

    def set_header_choices(self, values):
        self.h_header.set_choices(values)

    def set_data_size(self, rows, cols):
        self.setRowCount(rows)
        self.setColumnCount(cols)

    def current_header_values(self):
        return self.h_header.header_values()
