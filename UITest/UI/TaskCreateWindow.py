# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'TaskCreateWindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
from datetime import datetime

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QListWidgetItem, QMessageBox, QMenu, QAction


from UITest.UI.AddActionFlowDialog import NewActionFlowDialog, TaskActionFlow
from UITest.UI.TaskFlowCell import TaskFlowCell
from UITest import database
from UITest.database.Database import DataBasePool


class TaskCreateEntity:

    def __init__(self, tid, name, proxy_ip, port, task_url, profile_id, main_flow_id):
        self.name = name
        self.proxy_ip = proxy_ip
        self.port = port
        self.task_url = task_url
        self.profile_id = profile_id
        self.tid = tid
        self.main_flow_id = main_flow_id


mysql_pool = DataBasePool(host='localhost', port=3306, user='root', password='abc123456', db='load_emu')


# 查询新任务将使用的ID
def queryTaskID():
    rests = mysql_pool.query("SELECT MAX(id) as id FROM t_task;")
    print(rests)
    cout = len(rests)
    if cout == 0:
        return 1
    else:
        obj = rests[0]
        tid = obj['id']
        if tid is None:
            return 1
        else:
            return tid + 1


# 插入新任务
def insert_task(task: TaskCreateEntity):
    task_name = database.Database.escape_string(task.name)
    profile_id = database.Database.escape_string(task.profile_id)
    url = database.Database.escape_string(task.task_url)
    proxy_host = database.Database.escape_string(task.proxy_ip)
    proxy_port = database.Database.escape_string(task.port)

    tid = task.tid
    main_flow_id = task.main_flow_id

    sql = f'insert into t_task (id, task_name, profile_id, url, proxy_host, proxy_port, main_flow_id) values ({tid}, \'{task_name}\', \'{profile_id}\', \'{url}\', \'{proxy_host}\', \'{proxy_port}\', {main_flow_id});'
    mysql_pool.execute(sql)


# 更新任务
def update_task(task: TaskCreateEntity):
    task_name = database.Database.escape_string(task.name)
    profile_id = database.Database.escape_string(task.profile_id)
    url = database.Database.escape_string(task.task_url)
    proxy_host = database.Database.escape_string(task.proxy_ip)
    proxy_port = database.Database.escape_string(task.port)
    tid = task.tid
    main_flow_id = task.main_flow_id

    sql = f'update t_task set task_name=\'{task_name}\', profile_id=\'{profile_id}\', url=\'{url}\', proxy_host=\'{proxy_host}\', proxy_port=\'{proxy_port}\', main_flow_id={main_flow_id}  where id={tid};'
    mysql_pool.execute(sql)


# 查询任务所有流程
def query_all_flow(tid):
    sql = f'select * from t_task_flow where task_id={tid};'
    reslts = mysql_pool.query(sql)

    tmp_arr = []
    for dic0 in reslts:
        obj = TaskActionFlow(name=dic0['flow_name'], flow_id=dic0['id'], task_id=dic0['task_id'])
        tmp_arr.append(obj)

    return tmp_arr


# 删除任务下的所有流程
def rm_task_flow(tid):
    sql = f'select id from t_task_flow where task_id={tid};'
    ids = mysql_pool.query(sql)
    id_arr = []
    for dic0 in ids:
        did = dic0['id']
        id_arr.append(f'{did}')

    if len(id_arr) > 0:
        fids = ','.join(id_arr)
        clear_step_sql = f'delete from t_task_flow_step where flow_id in ({fids});'
        mysql_pool.execute(clear_step_sql)

    sql = f'delete from t_task_flow where task_id={tid};'
    mysql_pool.execute(sql)


# 删除整个流程，包括所有步骤
def rm_flow(fid):
    clear_step_sql = f'delete from t_task_flow_step where flow_id={fid};'
    mysql_pool.execute(clear_step_sql)

    sql = f'delete from t_task_flow where id={fid};'
    mysql_pool.execute(sql)


# 重置任务主流程
def clear_task_main_flow(tid):
    sql = f'update t_task set main_flow_id=0 where id={tid};'
    mysql_pool.execute(sql)


# 将分支流程从流程步骤中清除
def clear_flow_branch(fid):
    sql = f'update t_task_flow_step set turn_flow_id=0 where turn_flow_id={fid};'
    mysql_pool.execute(sql)


def check_text_empty(text):
    if text is None:
        return True
    else:
        c = len(text)
        if c == 0:
            return True
        else:
            return False


def alert_msg(parent, msg):
    QMessageBox.about(parent, '温馨提示', msg)


class TaskCreateDialog(QtWidgets.QDialog):

    def __init__(self, task_id=None, callback=None):
        super(TaskCreateDialog, self).__init__()
        self.callback = callback

        self.ui_flow_infos = dict()
        self.flow_item_infos = dict()
        self.new_flow_items = []
        self.flow_arr = []

        self.setupUi(self)
        self.setup_menu()
        self.is_edit = False
        if task_id is None:
            self.tid = queryTaskID()
            self.is_edit = False
        else:
            self.tid = task_id
            self.is_edit = True
            self.setup_edit_ui()

    def setup_edit_ui(self):
        sql = f'select * from t_task where id={self.tid};'
        rests = mysql_pool.query(sql)
        c = len(rests)
        if c == 0:
            return

        dic0 = rests[0]

        self.lineEdit.setText(dic0['task_name'])
        self.lineEdit_5.setText(dic0['proxy_host'])
        self.lineEdit_6.setText(dic0['proxy_port'])
        self.lineEdit_4.setText(dic0['url'])
        self.lineEdit_8.setText(dic0['profile_id'])

        flow_id = dic0['main_flow_id']
        self.lineEdit_9.setText(f'{flow_id}')

        flow_arr = query_all_flow(self.tid)
        for flow in flow_arr:
            self.display_flow(flow)

    def setup_menu(self):
        # 单击选中某一个选项
        self.listWidget.clicked.connect(self.on_check_row)

        # 窗口绑定右键事件
        self.window().setContextMenuPolicy(Qt.CustomContextMenu)
        self.window().customContextMenuRequested.connect(self.show_context_menu)

        # 创建QMenu
        self.contextMenu = QMenu(self)
        self.actionA = QAction("编辑")
        self.contextMenu.addAction(self.actionA)

        self.contextMenu.addSeparator()

        self.actionB = QAction("删除")
        self.contextMenu.addAction(self.actionB)

        # 点击menu
        self.actionA.triggered.connect(self.on_menu_edit_flow)
        self.actionB.triggered.connect(self.on_menu_rm_flow)

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(778, 536)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setMinimumSize(QtCore.QSize(80, 0))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.lineEdit = QtWidgets.QLineEdit(Dialog)
        self.lineEdit.setObjectName("lineEdit")
        self.horizontalLayout.addWidget(self.lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_5 = QtWidgets.QLabel(Dialog)
        self.label_5.setMinimumSize(QtCore.QSize(80, 0))
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_6.addWidget(self.label_5)
        self.lineEdit_5 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.horizontalLayout_6.addWidget(self.lineEdit_5)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_6 = QtWidgets.QLabel(Dialog)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_7.addWidget(self.label_6)
        self.lineEdit_6 = QtWidgets.QLineEdit(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_6.sizePolicy().hasHeightForWidth())
        self.lineEdit_6.setSizePolicy(sizePolicy)
        self.lineEdit_6.setMinimumSize(QtCore.QSize(80, 0))
        self.lineEdit_6.setObjectName("lineEdit_6")
        self.horizontalLayout_7.addWidget(self.lineEdit_6)
        self.horizontalLayout_6.addLayout(self.horizontalLayout_7)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_4 = QtWidgets.QLabel(Dialog)
        self.label_4.setMinimumSize(QtCore.QSize(80, 0))
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_5.addWidget(self.label_4)
        self.lineEdit_4 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.horizontalLayout_5.addWidget(self.lineEdit_4)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_8 = QtWidgets.QLabel(Dialog)
        self.label_8.setMinimumSize(QtCore.QSize(80, 0))
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_9.addWidget(self.label_8)
        self.lineEdit_8 = QtWidgets.QLineEdit(Dialog)
        self.lineEdit_8.setObjectName("lineEdit_8")
        self.horizontalLayout_9.addWidget(self.lineEdit_8)

        self.label_9 = QtWidgets.QLabel(Dialog)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_9.addWidget(self.label_9)
        self.lineEdit_9 = QtWidgets.QLineEdit(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEdit_9.sizePolicy().hasHeightForWidth())
        self.lineEdit_9.setSizePolicy(sizePolicy)
        self.lineEdit_9.setMinimumSize(QtCore.QSize(80, 0))
        self.lineEdit_9.setObjectName("lineEdit_9")
        self.horizontalLayout_9.addWidget(self.lineEdit_9)

        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.listWidget = QtWidgets.QListWidget(Dialog)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.pushButton_2 = QtWidgets.QPushButton(Dialog)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        spacerItem1 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.pushButton = QtWidgets.QPushButton(Dialog)
        self.pushButton.setMinimumSize(QtCore.QSize(100, 0))
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "新建任务"))
        self.label.setText(_translate("Dialog", "任务名称"))
        self.label_5.setText(_translate("Dialog", "代理IP"))
        self.label_6.setText(_translate("Dialog", "端口"))
        self.label_4.setText(_translate("Dialog", "任务链接"))
        self.label_8.setText(_translate("Dialog", "配置文件ID"))
        self.label_9.setText("主流程ID")

        self.pushButton_2.setText(_translate("Dialog", "新建流程"))
        self.pushButton.setText(_translate("Dialog", "保存"))

        self.pushButton_2.clicked.connect(self.add_action_flow)
        self.pushButton.clicked.connect(self.on_save)

    def add_action_flow(self):
        dialog = NewActionFlowDialog(task_id=self.tid, callback=self.on_new_flow)
        dialog.exec_()

    def on_save(self):
        print("点击保存任务")
        name = self.lineEdit.text()
        if check_text_empty(name):
            alert_msg(self, "请填写任务名称")
            return

        ip = self.lineEdit_5.text()
        if check_text_empty(ip):
            alert_msg(self, "请填写代理IP")
            return

        port = self.lineEdit_6.text()
        if check_text_empty(port):
            alert_msg(self, "请填写代理端口")
            return

        t_url = self.lineEdit_4.text()
        if check_text_empty(t_url):
            alert_msg(self, "请填写任务链接")
            return

        profile_id = self.lineEdit_8.text()
        if check_text_empty(profile_id):
            alert_msg(self, "请填写配置文件ID")
            return

        main_flow_id_str = self.lineEdit_9.text()
        if check_text_empty(main_flow_id_str):
            alert_msg(self, "请填写主流程ID")
            return

        main_flow_id = 0
        try:
            main_flow_id = int(main_flow_id_str)
        except Exception:
            alert_msg(self, "主流程ID必须为数字")
            return

        entity = TaskCreateEntity(tid=self.tid, name=name, proxy_ip=ip, port=port, task_url=t_url,
                                  profile_id=profile_id, main_flow_id=main_flow_id)

        if self.is_edit:
            update_task(entity)
        else:
            insert_task(entity)

        if self.callback is not None:
            self.callback(entity, self.is_edit)
        self.close()

    def on_new_flow(self, flow: TaskActionFlow, is_edit: bool):

        if not is_edit:
            print(f"新建流程 {flow.name}")
            self.new_flow_items.append(flow)
            self.display_flow(flow)
        else:
            cell: TaskFlowCell = self.ui_flow_infos[flow.flow_id]
            old_flow = self.flow_item_infos[flow.flow_id]
            self.flow_item_infos[flow.flow_id] = flow

            old_index = self.flow_arr.index(old_flow)
            self.flow_arr[old_index] = flow

            cell.id_lb.setText(f'{flow.flow_id}')
            cell.name_lb.setText(flow.name)

    def display_flow(self, flow: TaskActionFlow):
        item_widget = QListWidgetItem()
        item_widget.setSizeHint(QSize(self.listWidget.width(), 80))
        self.listWidget.addItem(item_widget)

        cell = TaskFlowCell()
        cell.id_lb.setText(f'{flow.flow_id}')
        cell.name_lb.setText(flow.name)

        self.ui_flow_infos[flow.flow_id] = cell
        self.flow_item_infos[flow.flow_id] = flow
        self.flow_arr.append(flow)

        self.listWidget.setItemWidget(item_widget, cell)

    def on_check_row(self, index):
        self.f = index.row()
        print(f"点击了行 {self.f}")

    def show_context_menu(self):

        items = self.listWidget.selectedItems()
        if len(items) > 0:
            # self.contextMenu.show()
            self.contextMenu.popup(QCursor.pos())  # 在鼠标位置显示
            self.contextMenu.show()

    def on_menu_edit_flow(self):
        print("点击右键菜单")
        # 获取数据
        flow = self.flow_arr[self.f]

        dialog = NewActionFlowDialog(task_id=self.tid, flow_id=flow.flow_id, callback=self.on_new_flow)
        dialog.exec_()

    def on_menu_rm_flow(self):
        print("点击删除任务")

        # 获取数据
        flow = self.flow_arr[self.f]

        # 删除数据
        self.ui_flow_infos[flow.flow_id] = None
        self.flow_item_infos[flow.flow_id] = None
        self.flow_arr.remove(flow)

        # 如果删除的是主流程，对应更新任务主流程
        main_txt = self.lineEdit_9.text()
        cur_fid = f'{flow.flow_id}'
        if main_txt == cur_fid:
            self.lineEdit_9.setText("")
            clear_task_main_flow(self.tid)

        # 如果删除流程是其它流程的分支，那么其它流程分支设置也将为空
        clear_flow_branch(flow.flow_id)

        # 删除流程
        rm_flow(flow.flow_id)

        # 更新界面
        self.listWidget.takeItem(self.f)