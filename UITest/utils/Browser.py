import time

from selenium import webdriver
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