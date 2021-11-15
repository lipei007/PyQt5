import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

import VMLogin
from NineOneOne import change_proxy, free_port
from VMLogin import getProfileInfos, editProfile, getDebugAddress
from random import randint, choice
import random


def shot(driver: webdriver, path):
    driver.save_screenshot(path)


# 模式手动输入
def type_words(element, string):
    for ch in string:
        time.sleep(0.1)
        element.send_keys(ch)


def randomMacAddress():
    # return '-'.join(re.findall('..', '%012x' % uuid.getnode())).upper()
    maclist = []
    for i in range(1, 7):
        randstr = "".join(random.sample("0123456789abcdef", 2))
        maclist.append(randstr)
    randmac = "-".join(maclist)
    return randmac.upper()


def randomComputerName():
    strings = 'abcdefghijklmnopqrstuvwxyz0123456789'
    tiles = ['PC', 'DESKTOP', '']
    pre = tiles[randint(0, 2)]
    if len(pre) > 0:
        pre = pre + '-'
    l = randint(5, 10)
    for i in range(0, l):
        s = choice(strings)
        pre = pre + s
    return pre.upper()


def random64Id():
    strings = 'abcdef0123456789'
    s = ''
    for i in range(0, 64):
        s = s + choice(strings)
    return s


def startBrowser(debug_address, url):
    # 设置配置
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", debug_address)
    chrome_driver = r"E:\ChromeDriver\90\chromedriver.exe"

    try:
        driver = webdriver.Chrome(chrome_driver, options=chrome_options)
        driver.get(url)
        return driver
    except:
        raise Exception("启动失败")
    return None


def doTry(proxy_exe, token, profile_id, country, state, city, platform, langHdr, accept_language, host, port, url,
          callback):
    # 修改代理
    change_proxy(exe_path=proxy_exe, country=country, state=state, city=city, port=port)
    resp = VMLogin.randomEditProfile(token=token, profile_id=profile_id, platform=platform, langHdr=langHdr,
                                     accept_language=accept_language, timeZone=None, proxyhost=host, port=port)
    debug_address = getDebugAddress(profile_id=profile_id)
    driver = None
    try:
        # 开启浏览器
        driver = startBrowser(debug_address=debug_address, url=url)
        # 外部调用
        callback(driver)
    except WebDriverException as e:
        print("启动浏览器发生异常")
        callback(None)
    finally:
        # 释放代理
        free_port(exe_path=proxy_exe, port=port)
        if driver is not None:
            driver.quit()
