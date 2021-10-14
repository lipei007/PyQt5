# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'AddActionFlowDialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QListWidgetItem, QMessageBox

import database.Database
from ActionStepCell import ActionSetpCell, TaskActionFlowStep


class TaskActionFlow:
    '''
    任务执行流程
    '''

    def __init__(self, name, flow_id, task_id):
        self.name = name
        self.flow_id = flow_id
        self.task_id = task_id


# 数据库连接池
from database.Database import DataBasePool

mysql_pool = DataBasePool(host='localhost', port=3306, user='root', password='abc123456', db='load_emu')


def queryFlowID():
    rests = mysql_pool.query("SELECT MAX(id) as id FROM t_task_flow;")
    print(rests)
    cout = len(rests)
    if cout == 0:
        return 1
    else:
        obj = rests[0]
        flow_id = obj['id']
        if flow_id is None:
            return 1
        else:
            return flow_id + 1


def insert_flow_step(step: TaskActionFlowStep, flow_id):
    print(f'动作 {step.step} Action: {step.action} Content: {step.content} 切换执行分支: {step.branch_flow_id}')

    content = step.content
    if content is None:
        content = ''
    content = database.Database.escape_string(content)

    field_val = step.field
    if field_val is None:
        field_val = ''
    field_val = database.Database.escape_string(field_val)

    turn_flow_id_text = step.branch_flow_id
    turn_flow_id = 0
    if turn_flow_id_text is not None:
        f_turn_id = 0
        try:
            f_turn_id = int(turn_flow_id_text)
        except Exception:
            f_turn_id = 0

        turn_flow_id = f_turn_id

    sql = f'INSERT INTO `t_task_flow_step` (flow_id, step, action, field_val,`value`, turn_flow_id) VALUES ({flow_id}, {step.step}, {step.action}, \'{field_val}\', \'{content}\', {turn_flow_id});'
    mysql_pool.execute(sql)


def update_flow_step(step: TaskActionFlowStep):
    print(f'更新动作 {step.step} Action: {step.action} Content: {step.content} 切换执行分支: {step.branch_flow_id}')

    content = step.content
    if content is None:
        content = ''
    content = database.Database.escape_string(content)

    field_val = step.field
    if field_val is None:
        field_val = ''
    field_val = database.Database.escape_string(field_val)

    turn_flow_id_text = step.branch_flow_id
    turn_flow_id = 0
    if turn_flow_id_text is not None:
        f_turn_id = 0
        try:
            f_turn_id = int(turn_flow_id_text)
        except Exception:
            f_turn_id = 0

        turn_flow_id = f_turn_id

    sql = f'update `t_task_flow_step` set step={step.step}, action={step.action}, field_val=\'{field_val}\',`value`=\'{content}\', turn_flow_id={turn_flow_id} where id={step.id};'
    mysql_pool.execute(sql)


def insert_flow(flow: TaskActionFlow):
    name = database.Database.escape_string(flow.name)

    sql = f'insert into t_task_flow (id, flow_name, task_id) values ({flow.flow_id}, \'{name}\', {flow.task_id});'
    mysql_pool.execute(sql)


def update_flow(flow: TaskActionFlow):
    name = database.Database.escape_string(flow.name)

    sql = f'update t_task_flow set flow_name=\'{name}\' where id={flow.flow_id};'
    mysql_pool.execute(sql)


def query_all_step(flow_id):
    sql = f'select * from t_task_flow_step where flow_id={flow_id};'
    arr = mysql_pool.query(sql)
    return arr


def query_flow_name(flow_id):
    sql = f'select flow_name from t_task_flow where id={flow_id};'
    arr = mysql_pool.query(sql)
    if len(arr) == 0:
        return ""
    dic0 = arr[0]
    return dic0["flow_name"]


# 查询表的所有字段
def query_all_columns(table):
    arr = mysql_pool.query(f'select COLUMN_NAME from information_schema.COLUMNS where table_name = \'{table}\';')
    tmp_arr = []
    for dic0 in arr:
        tmp_arr.append(dic0['COLUMN_NAME'])
    return tmp_arr


class NewActionFlowDialog(QtWidgets.QDialog):

    def __init__(self, task_id, flow_id=None, callback=None):
        super(NewActionFlowDialog, self).__init__()
        self.stepNum = 0
        self.contentH = 0
        self.stepArr = []
        self.task_id = task_id
        self.callback = callback
        self.setupUi(self)

        # self.columns = query_all_columns("us_data")
        # print(self.columns)

        self.pushButton_2.clicked.connect(self.on_add_step)
        self.pushButton.clicked.connect(self.on_save)

        if flow_id is None:
            self.flow_id = queryFlowID()
            self.is_edit = False
        else:
            self.flow_id = flow_id
            self.is_edit = True

            name = query_flow_name(flow_id)
            self.lineEdit.setText(name)

            arr = query_all_step(self.flow_id)
            for dic0 in arr:
                cell: ActionSetpCell = self.on_add_step()

                cell.edit_id = dic0['id']
                cell.comboBox.setCurrentIndex(dic0['action'])
                cell.lineEdit_2.setText(dic0['value'])

                field_val = dic0['field_val']
                if field_val is not None:
                    if len(field_val) > 0:
                        cell.field_comboBox.setCurrentText(field_val)

                turn_id = dic0['turn_flow_id']
                if turn_id != 0:
                    cell.lineEdit.setText(f'{turn_id}')
                else:
                    cell.lineEdit.setText("")

    def on_add_step(self):
        self.stepNum = self.stepNum + 1
        item_widget = QListWidgetItem()

        item_widget.setSizeHint(QSize(self.width(), 60))
        self.listWidget.addItem(item_widget)
        cell = ActionSetpCell(self.stepNum)
        self.listWidget.setItemWidget(item_widget, cell)
        self.contentH = self.contentH + 60
        self.stepArr.append(cell)
        return cell

    def on_save(self):

        name = self.lineEdit.text()
        if len(name) == 0:
            QMessageBox.about(self, '温馨提示', '请填写流程名称')
            return

        if self.stepNum == 0:
            QMessageBox.about(self, '温馨提示', '请添加执行动作')
            return

        print(f"流程名称: {name}")
        steps = []
        for stp in self.stepArr:
            step: TaskActionFlowStep = stp.build_step_for(0)
            if step is None:
                return
            steps.append(step)

            if step.id is None:
                insert_flow_step(step, flow_id=self.flow_id)
            else:
                update_flow_step(step)

        flow = TaskActionFlow(name=name, flow_id=self.flow_id, task_id=self.task_id)
        if self.is_edit:
            update_flow(flow)
        else:
            insert_flow(flow)

        self.callback(flow, self.is_edit)
        self.close()

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(670, 510)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setMinimumSize(QtCore.QSize(80, 0))
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout_2.addWidget(self.lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setMinimumSize(QtCore.QSize(0, 40))
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        spacerItem1 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setMinimumSize(QtCore.QSize(0, 40))
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "新建流程"))
        self.label.setText(_translate("Dialog", "流程名称"))
        self.pushButton_2.setText(_translate("Dialog", "添加动作"))
        self.pushButton.setText(_translate("Dialog", "保存"))