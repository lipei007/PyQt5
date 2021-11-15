import base64
from pyDes import *

Des_Key = "Fu*&@<FR"  # Key 长度为8
Des_IV = b"\x52\x63\x78\x61\xBC\x48\x6A\x07"  # 自定IV向量


# 加密
def encrpt(data):
    data = data.encode('utf-8')
    k = des(Des_Key, CBC, Des_IV, padmode=PAD_PKCS5)
    return base64.b64encode(k.encrypt(data)).decode("utf-8")


# 解密
def decrypt(data):
    data = data.encode('utf-8')
    k = des(Des_Key, CBC, Des_IV, padmode=PAD_PKCS5)
    return k.decrypt(base64.b64decode(data)).decode("utf-8")
