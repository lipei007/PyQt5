import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests

# 通过配置文件ID启动浏览器


def startBrowserByProfileId(profile_id, url):
    # 随机配置文件
    mla_url = 'https://api.vmlogin.com/v1/profile/start?automation=true&profileId=' + profile_id
    resp = requests.get(mla_url, timeout=10)
    json = resp.json()
    print(json['value'])

    # 设置配置
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", json['value'][7:])
    chrome_driver = ''

    # http://chromedriver.storage.googleapis.com/79.0.3945.36/chromedriver_win32.zip
    # 下载 chromedriver.exe 文件放到 python目录
    driver = webdriver.Chrome(chrome_driver, options=chrome_options)
    driver.get(url)
    executor_url = driver.command_executor._url
    session_id = driver.session_id
    print(executor_url)
    print(session_id)
    print('ok it is done')
    driver.quit()


# 获取debug地址
def getDebugAddress(profile_id):
    mla_url = 'http://127.0.0.1:35000/api/v1/profile/start?automation=true&profileId=' + profile_id
    resp = requests.get(mla_url, timeout=10)
    jsn = resp.json()
    return jsn['value'][7:]


# 随机配置文件
# platform: Windows Linux Macintosh Android iPhone Chrome Firefox Edge
# langHdr: en-US
# acceptLanguage: en-US,en;q=0.9
# timeZone: America/New_York
def randomProfile(platform, langHdr, accept_language, timeZone):
    data = {
        'platform': platform,
        'langHdr': langHdr,
        'acceptLanguage': accept_language
    }

    if timeZone is not None:
        data['timeZone'] = timeZone

    mla_url = 'http://127.0.0.1:35000/api/v1/profile/randomProfile'
    resp = requests.get(mla_url, data=data, timeout=10)
    jsn = resp.json()
    return jsn


# 获取配置文件信息
def getProfileInfos(token, profile_id):
    url = "https://api.vmlogin.com/v1/profile/detail?token=" + token + "&profileId=" + profile_id
    resp = requests.get(url, timeout=10)
    json = resp.json()
    return json


# 修改配置文件，语音设置微en-US, 时区基于IP，并设置代理
def editProfile(token, profile_id, jsn, host, port):
    jsn["acceptLanguage"] = "en-US,en;q=0.9"
    jsn["langHdr"] = "en-US"
    # 高级指纹保护设置 -> 启用基于IP设置时区
    jsn["timeZoneFillOnStart"] = True

    # 代理
    dic = dict(setProxyServer=True, type="SOCKS5", host=host, port=port)
    jsn["proxyServer"] = dic

    data = {
        'token': token,
        'profileId': profile_id,
        'Body': jsn
    }
    resp = requests.post(url="https://api.vmlogin.com/v1/profile/update", json=data, timeout=10)


# 获取所有可用浏览器配置文件的列表
# {
#             "sid":"95A3C227-FA97-42A7-B6A5-9316687F72B2",
#             "name":"008",
#             "tag":"Default group",
#             "lastUsedTime":1631366082
#         }
def getProfileList(token):
    url = "https://api.vmlogin.com/v1/profile/list?token=" + token
    resp = requests.get(url, timeout=10)
    jsn = resp.json()
    return jsn["data"]


# 释放配置文件浏览器
def releaseProfileBrowser(profile_id):

    mla_url = 'http://127.0.0.1:35000/api/v1/profile/stop?profileId=' + profile_id
    resp = requests.get(mla_url, timeout=10)
    jsn = resp.json()
    print("释放配置文件浏览器，返回结果\n" + json.dumps(jsn))
    return jsn


def createLocalProfileAndStart(platform, langHdr, accept_language, timeZone):
    profile = randomProfile(platform, langHdr, accept_language, timeZone)
    data = {
        'Body': profile
    }
    mla_url = 'http://127.0.0.1:35000/api/v1/profile/create_start'
    resp = requests.post(mla_url, data=data, timeout=10)
    jsn = resp.json()
    return jsn


# 随机更新配置文件
def randomEditProfile(token, profile_id, platform, langHdr, accept_language, timeZone, proxyhost, port):
    jsn = getProfileInfos(token, profile_id=profile_id)

    print("修改前配置：\n" + json.dumps(jsn))

    rdm = randomProfile(platform=platform, langHdr=langHdr, accept_language=accept_language, timeZone=timeZone)

    # 修改代理
    proxy = {
        "proxyPass": "",
        "proxyUser": "",
        "proxyPort": port,
        "proxyHost": proxyhost,
        "proxyType": "SOCKS5",
        "proxyServer": {
            "setProxyServer": True,
            "type": "SOCKS5",
            "password": "",
            "username": "",
            "port": port,
            "host": proxyhost
        }
    }

    for k, v in proxy.items():
        jsn[k] = v

    # leakProof
    leakProof = {
        "computerName": Browser.randomComputerName(),
        "macAddress": Browser.randomMacAddress()
    }

    # WebRTC
    webRtc_plat = {
        "type": "FAKE",
        "fillOnStart": True,
        "wanSet": True,
        "lanSet": True
    }
    webRtc = rdm["webRtc"]
    for k, v in webRtc_plat.items():
        webRtc[k] = v

    # Other
    jsn['hardwareConcurrency'] = rdm['hardwareConcurrency']
    jsn['platform'] = rdm['platform']
    jsn['userAgent'] = rdm['userAgent']
    jsn['screenHeight'] = rdm['screenHeight']
    jsn['screenWidth'] = rdm['screenWidth']
    jsn['langHdr'] = rdm['langHdr']
    jsn['webgl'] = rdm['webgl']
    jsn['acceptLanguage'] = rdm['acceptLanguage']
    jsn['timeZoneFillOnStart'] = True
    jsn['timeZone'] = ''
    jsn['webRtc'] = webRtc
    jsn['leakProof'] = leakProof

    # mediaDevices
    mediaDevices = rdm['mediaDevices']
    videoInputs = mediaDevices['videoInputs']
    audioInputs = mediaDevices['audioInputs']
    audioOutputs = mediaDevices['audioOutputs']

    mediaDevices_tmp = {
        "setMediaDevices": True,
        "use_name": False,
        "list": {
        },
        "videoInputs": videoInputs,
        "audioInputs": audioInputs,
        "audioOutputs": audioOutputs
    }

    lst = dict()
    if videoInputs > 0:
        lst['videoInputs'] = makeDevice(videoInputs)

    if audioInputs > 0:
        lst['audioInputs'] = makeDevice(audioInputs)

    if audioOutputs > 0:
        lst['audioOutputs'] = makeDevice(audioOutputs)

    mediaDevices_tmp['list'] = lst
    jsn['mediaDevices'] = mediaDevices_tmp

    print("随机配置文件:\n" + json.dumps(jsn))
    data = {
        'token': token,
        'profileId': profile_id,
        'Body': jsn
    }
    resp = requests.post(url="https://api.vmlogin.com/v1/profile/update", json=data, timeout=10)


def makeDevice(count):
    dic_tmp = dict()
    for i in range(0, count):
        dic_tmp[f'device{i + 1}'] = {
            "label": "n/a",
            "deviceId": Browser.random64Id(),
            "groupId": Browser.random64Id()
        }
    return dic_tmp
