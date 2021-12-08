import random
import sys
import time
import traceback
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as Expect
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains

from UITest.UI import TableFields
from UITest import database
from UITest.database.Database import DataBasePool
from UITest.utils import VMLogin
from UITest.utils.NineOneOne import change_proxy, free_port
from UITest.UI import Config

from PyQt5.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal, QThreadPool, QTimer

mysql_pool = DataBasePool(host='localhost', port=3306, user='root', password='abc123456', db='load_emu')


def query_flow(fid):
    name_sql = f'select flow_name from t_task_flow where id={fid};'
    res = mysql_pool.query(name_sql)
    name = None
    if len(res) == 0:
        return None
    else:
        name = res[0]['flow_name']

    step_sql = f'select * from t_task_flow_step where flow_id={fid} order by step asc;'
    res = mysql_pool.query(step_sql)
    return name, res


class TaskWorkerSignal(QObject):
    finished = pyqtSignal(int)  # 任务结束
    error = pyqtSignal(tuple)  # 任务错误
    step = pyqtSignal(str)  # 任务步骤
    no_data = pyqtSignal(int)  # 没有数据


class TaskWorker(QRunnable):

    def __init__(self, tid):
        super(TaskWorker, self).__init__()
        self.setAutoDelete(True)
        self.is_running = False
        self.is_cancel = False

        self.driver: webdriver = None
        self.main_steps = None
        self.t_name = None
        self.proxy_host = None
        self.proxy_port = None
        self.url = None
        self.profile_id = None
        self.flow_id = None

        self.logs = []
        self.data = None

        self.wait_next = False
        self.tid = tid
        self.signals = TaskWorkerSignal()

    @pyqtSlot()
    def run(self) -> None:
        self.is_running = True
        if self.is_cancel:
            self.is_cancel = True
            self.finished()
            return

        sql = f'select * from t_task where id={self.tid};'
        rests = mysql_pool.query(sql)
        c = len(rests)
        if c == 0:
            self.log(f"任务 {self.tid} 不存在")
            self.is_cancel = True
            self.finished()
            return

        dic0 = rests[0]

        self.t_name = dic0['task_name']
        self.proxy_host = dic0['proxy_host']
        self.proxy_port = dic0['proxy_port']
        self.url = dic0['url']
        self.profile_id = dic0['profile_id']
        self.flow_id = dic0['main_flow_id']

        if self.flow_id == 0:
            self.log(f"任务 {self.tid} 请设置主流程")
            self.is_cancel = True
            self.finished()
            return

        # 读取流程
        name, steps = query_flow(self.flow_id)
        if name is None:
            self.log(f"任务 {self.tid} 主流程无效")
            self.is_cancel = True
            self.finished()
            return

        self.main_steps = steps
        self.start_task()

    def log(self, msg):
        if msg is None:
            return
        self.logs.append(msg + '\n')
        print(msg)

    def save_logs(self, file_name):
        import os
        root = os.getcwd()

        log_dir = os.path.join(root, '../log')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        path = os.path.join(log_dir, file_name)
        with open(path, 'w', encoding='utf-8') as f:
            for line in self.logs:
                f.write(line)

    def stop_task(self, msg):
        self.log(msg)
        self.signals.no_data.emit(self.tid)

    def finished(self):
        self.is_running = False

        import datetime
        now_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(now_time, '%Y-%m-%d_%H_%M_%S')

        file_name = f"任务{self.tid}_{time_str}.log"
        if self.is_cancel:
            file_name = f"取消_任务{self.tid}_{time_str}.log"

        self.save_logs(file_name)
        self.signals.finished.emit(self.tid)

    def do_next(self):
        self.log(f"任务{self.tid} 等待执行下一条资料")
        time.sleep(random.randint(10, 20))
        self.start_task()

    def prepare_data(self):
        self.log(f"任务{self.tid} 开始准备数据")
        # 获取资料
        sql = f'select task_data_id from t_task_record  where task_id={self.tid} order by task_data_id desc limit 1 ;'
        result = mysql_pool.query(sql)

        data_id = None
        if len(result) > 0:
            # 最后一次执行任务的资料ID
            data_id = result[0]['task_data_id']

        if data_id is None:
            data_id = 0
        sql = f'select * from us_data where id > {data_id} limit 1;'
        datas = mysql_pool.query(sql)
        if len(datas) > 0:
            self.data = datas[0]

    def update_task_record_status(self, status):
        data_id = self.data['id']
        sql = f'update t_task_record set task_status={status} where task_id={self.tid} and task_data_id={data_id};'
        mysql_pool.execute(sql)

    def do_task_record_data_success(self):
        sql = f'update t_task set success_num=success_num+1 where id={self.tid};'
        mysql_pool.execute(sql)

        data_id = self.data['id']
        sql = f'update t_task_record set data_status=1 where task_id={self.tid} and task_data_id={data_id};'
        mysql_pool.execute(sql)

    def start_task(self):

        sql = f'select * from t_task where id={self.tid};'
        rests = mysql_pool.query(sql)
        c = len(rests)
        if c == 0:
            self.finished()
            return
        dic0 = rests[0]
        status = dic0.get('is_running', 0)
        if status == 0:
            self.is_cancel = True

        if self.is_cancel:
            self.finished()
            return

        # 准备数据
        self.prepare_data()
        if self.data is None:
            self.log(f"任务{self.tid} 没有可执行数据")
            self.is_cancel = True
            self.signals.no_data.emit(self.tid)
            return

        # 添加任务记录
        data_id = self.data['id']
        sql = f'insert into t_task_record (task_id, task_url, task_data_id, task_status) values ({self.tid}, \'{database.Database.escape_string(self.url)}\', {data_id}, {0});'
        mysql_pool.execute(sql)

        sql = f'update t_task set do_num=do_num+1 where id={self.tid};'
        mysql_pool.execute(sql)

        # 设置代理启动浏览器
        country = self.data.get('country')
        state = self.data.get('state')
        city = self.data.get('city')

        result, driver = self.start_browser(0, Config.Proxy_API, Config.VM_Token, self.profile_id, country=country,
                                            state=state,
                                            city=city, platform='Windows', langHdr='en-US',
                                            accept_language='en-US,en;q=0.9', host=self.proxy_host,
                                            port=self.proxy_port, url=self.url)

        if result == 1 and driver is not None:  # 启动浏览器无异常
            time.sleep(10)
            self.do_steps(self.tid, self.main_steps, driver)
        elif result == 3:
            self.update_task_record_status(2)
            self.register_next()

        # # 开始执行
        # driver = webdriver.Chrome()
        # driver.get(self.url)
        #
        # time.sleep(10)
        # self.do_steps(self.tid, self.main_steps, driver)

    # 释放端口并退出浏览器
    def release_port_and_quit(self, profile_id, proxy_exe, port):
        driver = self.driver

        if Config.Browser_Type == Config.Browser_Type_VMLogin:
            # 释放代理
            free_port(exe_path=proxy_exe, port=port)
            VMLogin.releaseProfileBrowser(profile_id)
        else:
            # 退出
            if driver is not None:
                driver.quit()
            # driver.service.stop()
        self.driver = None

    def start_browser(self, times, proxy_exe, token, profile_id, country, state, city, platform, langHdr,
                      accept_language, host,
                      port, url):

        result = 0
        driver = None
        try:
            # 修改代理
            if Config.Proxy_Type == Config.Proxy_Type_911S5:  # 911S5
                change_proxy(exe_path=proxy_exe, country=country, state=state, city=city, port=port)

            # 设置配置
            chrome_options = Options()
            if Config.Browser_Type == Config.Browser_Type_VMLogin:  # VMLogin
                # 随机VMLogin配置文件
                resp = VMLogin.randomEditProfile(token=token, profile_id=profile_id, platform=platform, langHdr=langHdr,
                                             accept_language=accept_language, timeZone=None, proxyhost=host, port=port)
                # 获取配置文件调试地址
                debug_address = VMLogin.getDebugAddress(profile_id=profile_id)
                chrome_options.add_experimental_option("debuggerAddress", debug_address)

            # 开启浏览器
            chrome_driver = Config.Chrome_Driver
            driver = webdriver.Chrome(chrome_driver, options=chrome_options)

            self.log("准备打开网页")
            driver.get(url)
            self.log("浏览器启动成功")
            result = 1
            self.driver = driver

        except:

            self.release_port_and_quit(profile_id, proxy_exe, port)

            if times >= 3:
                self.log(f"任务{id}，浏览器启动失败，超出重试次数")
                result = 3

            else:
                self.log(f"任务{id}，浏览器启动失败，等待五秒，重试端口: {port} 第 {times + 1} 次")
                time.sleep(5)
                result = 2

            driver = None

        if result == 2:
            return self.start_browser(times=times + 1, proxy_exe=proxy_exe, token=token, profile_id=profile_id,
                                      country=country, state=state,
                                      city=city, platform=platform, langHdr=langHdr, accept_language=accept_language,
                                      host=host,
                                      port=port, url=url)

        return result, driver

    def start_flow(self, tid, fid, driver):
        # 读取流程
        name, steps = query_flow(fid)
        if name is None:
            self.close_driver(driver, f"任务 {tid} 主流程 {fid} 无效, 关闭浏览器")
            self.stop_task("停止任务")
            return

        self.do_steps(tid, steps, driver)

    def close_driver(self, driver, msg):
        # driver.quit()
        self.release_port_and_quit(self.profile_id, Config.Proxy_API, self.proxy_port)
        if msg is not None:
            self.log(msg)

    # 模式手动输入
    def type_words(self, element, string):
        for ch in string:
            time.sleep(0.3)
            element.send_keys(ch)

    def do_steps(self, tid, steps, driver):
        el = None
        for step in steps:
            if self.is_cancel:
                self.close_driver(driver, f"取消执行任务， 关闭浏览器")
                self.stop_task("任务停止")
                return

            flow_id = step['flow_id']
            step_index = step['step']
            action = step['action']
            vl = step['value']
            turn_to = step['turn_flow_id']
            field = step['field_val']

            try:
                if action == 1:  # 成功任务
                    self.do_task_record_data_success()

                elif action == 2:  # 查找元素XPath
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素XPath，没有设置xpath值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return
                    self.log(f"流程{flow_id} 执行步骤{step_index}，查找元素XPath，{vl}")
                    el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.XPATH, vl)))
                    ActionChains(driver).move_to_element(el).perform()

                elif action == 3:  # 查找元素ID
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素ID，没有设置ID值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.log(f"流程{flow_id} 执行步骤{step_index}，查找元素ID，{vl}")
                    el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.ID, vl)))
                    ActionChains(driver).move_to_element(el).perform()

                elif action == 4:  # 查找元素Name
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素Name，没有设置Name值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.log(f"流程{flow_id} 执行步骤{step_index}，查找元素Name，{vl}")
                    el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.NAME, vl)))
                    ActionChains(driver).move_to_element(el).perform()

                elif action == 5:  # 查找元素CSS Selector
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素Name，没有设置CSS值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.log(f"流程{flow_id} 执行步骤{step_index}，查找元素CSS，{vl}")

                    # css selector常用符号;
                    # . 表示class
                    # # 表示id
                    # > 表示子元素，层级
                    el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.CSS_SELECTOR, vl)))
                    ActionChains(driver).move_to_element(el).perform()

                elif action == 6:  # 查找元素Text
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素LinkText，没有设置Text值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.log(f"流程{flow_id} 执行步骤{step_index}，查找元素LinkText，{vl}")
                    el = WebDriverWait(driver, 10, 0.5).until(
                        Expect.presence_of_element_located((By.PARTIAL_LINK_TEXT, vl)))
                    ActionChains(driver).move_to_element(el).perform()

                elif action == 7:  # 查找元素文字
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素文字，没有设置文字值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.log(f"流程{flow_id} 执行步骤{step_index}，查找元素文字，{vl}")
                    els = driver.find_elements_by_xpath(f"//*[contains(text(),'{vl}')]")
                    el = None
                    for e in els:
                        if e.is_displayed():
                            el = e
                            continue
                    if el is not None:
                        ActionChains(driver).move_to_element(el).perform()

                elif action == 8:  # 点击
                    if el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，点击，没有找到元素, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.log(f"流程{flow_id} 执行步骤{step_index} 点击")
                    el.click()

                elif action == 9:  # 输入
                    if el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，输入，没有找到元素, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    input_str = vl
                    if vl is None:
                        input_str = ''

                    self.log(f"流程{flow_id} 执行步骤{step_index} 输入 字段 {field} 值 {vl}")

                    if field is not None:
                        if len(field) > 0:
                            column_name = TableFields.maps.get(field, None)
                            if column_name is not None:  # 输入的是数据库中存的数据，column_name为字段
                                input_str = self.data.get(column_name, vl)

                    if input_str is not None:
                        input_str = f'{input_str}'

                    if input_str is None or len(input_str) == 0:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，输入，没有设置输入值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    self.type_words(el, input_str)
                    # el.send_keys(input_str)

                elif action == 10:  # 选择
                    if el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，选择，没有找到元素, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    lst_n = None
                    if vl is not None and len(vl) > 0:
                        vl_str = str(vl).replace('，', ',')  # 中文逗号转英文逗号
                        vl_str = vl_str.replace(' ', '')  # 剔除空格
                        arr = vl_str.split(',')
                        tmp_arr = []

                        # 将输入的索引转为整数
                        for s in arr:
                            try:
                                i = int(s)
                                tmp_arr.append(i)
                            except:
                                pass

                        # 随机获取索引
                        if len(tmp_arr) > 0:
                            lst_n = tmp_arr[random.randint(0, len(tmp_arr) - 1)]
                            try:
                                lst_n = int(lst_n)
                            except:
                                print(f"lst_n = {lst_n}")
                                lst_n = None

                    s = Select(el)
                    l = len(s.options)
                    if not (lst_n is not None and 0 <= lst_n < l):
                        lst_n = random.randint(0, l - 1)
                    self.log(f"流程{flow_id} 执行步骤{step_index} Select随机选择索引 {lst_n}")
                    s.select_by_index(lst_n)

                elif action == 11:  # 强制等待
                    seconds = 10
                    if vl is not None:
                        try:
                            seconds = int(vl)
                        except Exception:
                            seconds = 10
                    self.log(f"流程{flow_id} 执行步骤{step_index} 强制等待 {seconds}秒")
                    time.sleep(seconds)

                elif action == 12:  # 输入随机数
                    if el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，输入，没有找到元素, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常, 没有设置随机数范围， 关闭浏览器")
                        self.stop_task("任务停止")
                        return
                    vl_str = str(vl)
                    vl_str = vl_str.replace(' ', '')
                    vl_str = vl_str.replace('，', ',')
                    arr = vl_str.split(',')
                    if len(arr) < 2:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常, 设置随机数格式不正确， 关闭浏览器")
                        self.stop_task("任务停止")
                        return
                    v0 = int(arr[0])
                    v1 = int(arr[1])
                    if v0 > v1:
                        tmp = v0
                        v0 = v1
                        v1 = tmp
                    r = random.randint(v0, v1)
                    if r > 100:
                        r = int(r / 100)
                        r = r * 100

                    self.log(f"流程{flow_id} 执行步骤{step_index} 随机输入 {r}")
                    self.type_words(el, f'{r}')

                elif action == 13:  # 选择Value
                    if el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，选择Value，没有找到元素, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    input_str = vl
                    if vl is None:
                        input_str = ''

                    self.log(f"流程{flow_id} 执行步骤{step_index} 选择Value 字段 {field} 值 {vl}")

                    if field is not None:
                        if len(field) > 0:
                            column_name = TableFields.maps.get(field, None)
                            if column_name is not None:  # 输入的是数据库中存的数据，column_name为字段
                                input_str = self.data.get(column_name, vl)

                    if input_str is None or len(input_str) == 0:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，选择Value，没有设置值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    s = Select(el)
                    s.select_by_value(input_str)

                elif action == 14:  # 选择Text
                    if el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，选择Text，没有找到元素, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    input_str = vl
                    if vl is None:
                        input_str = ''

                    self.log(f"流程{flow_id} 执行步骤{step_index} 选择Text 字段 {field} 值 {vl}")

                    if field is not None:
                        if len(field) > 0:
                            column_name = TableFields.maps.get(field, None)
                            if column_name is not None:  # 输入的是数据库中存的数据，column_name为字段
                                input_str = self.data.get(column_name, vl)

                    if input_str is None or len(input_str) == 0:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，选择Text，没有设置值, 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    s = Select(el)
                    s.select_by_visible_text(input_str)

                elif action == 15:  # 跳转流程
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常, 跳转流程没设置流程ID， 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    try:
                        turn_to = int(vl)
                        if turn_to == 0:
                            self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，跳转流程ID为0, 关闭浏览器")
                            self.stop_task("任务停止")

                        else:
                            self.log(f"流程{flow_id} 执行步骤{step_index}，跳转流程 {turn_to}")
                            self.start_flow(tid, turn_to, driver)

                    except:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，跳转流程ID错误, 关闭浏览器")
                        self.stop_task("任务停止")

                    return
                elif action == 16:  # 切换到新窗口
                    self.log(f"流程{flow_id} 执行步骤{step_index}，切换窗口")

                    cur_handle = driver.current_window_handle
                    cur_url = driver.current_url
                    cur_host = urlparse(cur_url).netloc

                    handles = driver.window_handles()
                    if len(handles) <= 1:
                        self.log(f"流程{flow_id} 执行步骤{step_index}，无其他窗口可切换")
                        continue

                    to_hd = None
                    for hd in handles:
                        driver.switch_to_window(hd)
                        hd_url = driver.current_url
                        hd_host = urlparse(hd_url).netloc
                        if hd != cur_handle and hd_host == cur_host:
                            to_hd = hd
                            break

                    if to_hd is not None:  # 可以切换
                        for hd in handles:
                            driver.switch_to_window(hd)
                            if hd != to_hd:  # 关闭窗口
                                driver.close()

                        # 最终切换到目标窗口
                        driver.switch_to_window(to_hd)
                        self.log(f"流程{flow_id} 执行步骤{step_index}，关闭其他窗口，成功切换到目标窗口")

                elif action == 17:  # 删除只读属性
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 删除只读属性ByID， 没有设置ID值， 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    js_script = f'document.getElementById(\"{vl}\").removeAttribute("readonly");'
                    driver.execute_script(js_script)

                    self.log(f"流程{flow_id} 执行步骤{step_index} 执行JS脚本 删除只读属性ByID {vl}")

                elif action == 18:  # 选择日期
                    if vl is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 查找日期值， 没有设置XPath， 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    date_elements = driver.find_elements_by_xpath(vl)
                    if len(date_elements) == 0:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 查找日期值， 没找到任何元素， 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    random_day = random.randint(20, 28)

                    self.log(f"流程{flow_id} 执行步骤{step_index} 随机选择日期 {random_day}")

                    day_el = None
                    for elment in date_elements:
                        date_text = elment.text
                        if date_text == f'{random_day}':
                            day_el = elment
                            break

                    if day_el is None:
                        self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 查找日期值， 没找到合适的日期， 关闭浏览器")
                        self.stop_task("任务停止")
                        return

                    # location_x, location_y = day_el.location.values()
                    # ActionChains(driver).move_by_offset(location_x, location_y).click().perform()
                    ActionChains(driver).move_to_element(day_el).click().perform()

                else:  # 未知操作
                    self.update_task_record_status(2)
                    self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，未知操作, 关闭浏览器")
                    self.stop_task("任务停止")

            except:

                if turn_to is not None:
                    if turn_to != 0:
                        self.log(f"流程{flow_id} 执行步骤{step_index} 异常，转向流程 {turn_to}")
                        self.start_flow(tid, turn_to, driver)
                        return

                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.log(f"流程{flow_id} 执行步骤{step_index} 异常:\n{exctype} {value} {traceback.format_exc()}")

                if value is NoSuchWindowException:  # 浏览器窗口被关闭了
                    self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 浏览器窗口被关闭")
                else:
                    # self.close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，抛出异常")
                    time.sleep(60)

                # 执行下一个
                self.update_task_record_status(2)
                self.register_next()
                return

        wait_ex = random.randint(6, 12)
        self.log(f"任务 {self.tid} 执行完成, 等待{wait_ex}秒，再执行下次")
        time.sleep(wait_ex)
        self.close_driver(driver, f"流程{flow_id} 执行完成， 关闭浏览器")

        # 下一个
        self.update_task_record_status(1)
        self.register_next()

    def register_next(self):
        self.log(f"任务{self.tid} 进入等待状态")
        self.wait_next = True

    def on_timer_triggered(self):
        self.do_next()


class TaskWorkerDispatcherSignal(QObject):
    next_worker = pyqtSignal(TaskWorker)  # 更新任务worker
    finished = pyqtSignal(int)  # 任务执行完成


class TaskWorkerDispatcher(QObject):

    def __init__(self):
        super(TaskWorkerDispatcher, self).__init__()
        self.thread_pool = QThreadPool()

        self.workers = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_triggered)
        self.timer.start(5000)

        self.signals = TaskWorkerDispatcherSignal()

    def build_task_worker(self, tid):
        worker = TaskWorker(tid)
        worker.signals.no_data.connect(self.on_task_no_data)
        return worker

    def start_task(self, worker: TaskWorker):
        if worker is None:
            return
        self.thread_pool.start(worker)
        self.workers.append(worker)

    def stop_task(self, tid):
        for worker in self.workers:
            if worker.tid == tid:
                worker.is_cancel = True
                return

    def on_task_no_data(self, tid):
        self.signals.finished.emit(tid)

    def on_timer_triggered(self):

        rm_workers = []

        for worker in self.workers:
            if worker.wait_next or worker.is_cancel:
                rm_workers.append(worker)

        for wk in rm_workers:
            tid = wk.tid
            wk.log(f"任务 {tid} 即将再次执行")
            wk.finished()
            self.workers.remove(wk)

            if wk.wait_next:
                worker = self.build_task_worker(tid)
                self.signals.next_worker.emit(worker)
