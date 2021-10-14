import random
import sys
import time
import traceback

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as Expect
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from database.Database import DataBasePool


def test():
    '''

    find_by_xpath
    find_by_id
    find_by_name

    wait

    click
    select
    send

    '''

    arr = [0, 1, 2, 3, 4, 5, 6]
    count = len(arr)
    i = 0
    while i < count:
        opt = arr[i]
        if opt == 0:
            pass
        elif opt == 1:
            pass
        elif opt == 2:
            pass
        elif opt == 3:
            pass
        elif opt == 4:
            pass
        elif opt == 5:
            pass
        elif opt == 6:
            pass
        i = i + 1


def startPiepline():
    driver = webdriver.Chrome()
    driver.get("http://sahitest.com/demo/formTest.htm")


mysql_pool = DataBasePool(host='localhost', port=3306, user='root', password='abc123456', db='load_emu')


def query_flow(fid):
    name_sql = f'select flow_name from t_task_flow where id={fid};'
    res = mysql_pool.query(name_sql)
    name = None
    if len(res) == 0:
        return None
    else:
        name = res[0]['flow_name']

    step_sql = f'select * from t_task_flow_step where flow_id={fid};'
    res = mysql_pool.query(step_sql)
    return name, res


def startTask(tid):
    sql = f'select * from t_task where id={tid};'
    rests = mysql_pool.query(sql)
    c = len(rests)
    if c == 0:
        return

    dic0 = rests[0]

    name = dic0['task_name']
    proxy_host = dic0['proxy_host']
    proxy_port = dic0['proxy_port']
    url = dic0['url']
    profile_id = dic0['profile_id']
    flow_id = dic0['main_flow_id']

    if flow_id == 0:
        print(f"任务 {tid} 请设置主流程")
        return

    # 读取流程
    name, steps = query_flow(flow_id)
    if name is None:
        print(f"任务 {tid} 主流程无效")
        return

    driver = webdriver.Chrome()
    driver.get(url)

    time.sleep(10)
    do_steps(tid, steps, driver)


def start_flow(tid, fid, driver):
    # 读取流程
    name, steps = query_flow(fid)
    if name is None:
        close_driver(driver, f"任务 {tid} 主流程 {fid} 无效")
        return

    do_steps(tid, steps, driver)


def close_driver(driver, msg):
    driver.quit()
    if msg is not None:
        print(msg)


def do_steps(tid, steps, driver):
    el = None
    for step in steps:
        flow_id = step['flow_id']
        step_index = step['step']
        action = step['action']
        vl = step['value']
        turn_to = step['turn_flow_id']

        try:
            if action == 1:

                if vl is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素XPath，没有设置xpath值")
                    return
                print(f"流程{flow_id} 执行步骤{step_index}，查找元素XPath，{vl}")
                el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.XPATH, vl)))
            elif action == 2:
                if vl is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素ID，没有设置ID值")
                    return

                print(f"流程{flow_id} 执行步骤{step_index}，查找元素ID，{vl}")
                el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.ID, vl)))

            elif action == 3:
                if vl is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，查找元素Name，没有设置Name值")
                    return

                print(f"流程{flow_id} 执行步骤{step_index}，查找元素Name，{vl}")
                el = WebDriverWait(driver, 10, 0.5).until(Expect.presence_of_element_located((By.NAME, vl)))
            elif action == 4:
                if el is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，点击，没有找到元素")
                    return

                print(f"流程{flow_id} 执行步骤{step_index} 点击")
                el.click()
            elif action == 5:
                if el is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，输入，没有找到元素")
                    return

                if vl is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，输入，没有设置输入值")
                    return

                print(f"流程{flow_id} 执行步骤{step_index} 输入 {vl}")
                el.send_keys(vl)
            elif action == 6:
                if el is None:
                    close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，选择，没有找到元素")
                    return

                s = Select(el)
                l = len(s.options)
                random_indx = random.randint(0, l-1)
                print(f"流程{flow_id} 执行步骤{step_index} Select随机选择")
                s.select_by_index(random_indx)
            elif action == 7:
                seconds = 10
                if vl is not None:
                    try:
                        seconds = int(vl)
                    except Exception:
                        seconds = 10
                time.sleep(seconds)

            else:
                close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，未知操作")

        except Exception as e:

            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]

            if turn_to is not None:
                if turn_to != 0:
                    print(f"流程{flow_id} 执行步骤{step_index} 异常，转向流程 {turn_to}")
                    start_flow(tid, turn_to, driver)
                    return

            close_driver(driver, f"流程{flow_id} 执行步骤{step_index} 异常，抛出异常")
            return

    time.sleep(15)
    close_driver(driver, "执行完成")
