# -*- coding: utf-8 -*-
import math
import base64
import random
from typing import Dict

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def get_i(a: int) -> str:
    """
    生成长度为16的随机key
    :param a:
    :return:
    """
    d = 0
    b = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    c = ""
    while d < a:
        e = random.random() * len(b)
        e = math.floor(e)
        c += b[e]
        d += 1

    return c

def get_b(a: str, b: str) -> str:
    """
    AES加密实现
    :param a:
    :param b:
    :return:
    """
    key = b.encode("utf-8")
    iv = "0102030405060708".encode("utf-8")
    encode_plaintext = a.encode("utf-8")
    cipher_unit = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = pad(encode_plaintext, AES.block_size)
    cipher_text = cipher_unit.encrypt(padded_plaintext)
    return base64.b64encode(cipher_text).decode("utf-8")

def encrypted_string(b, p, m) -> str:
    d = len(b)
    radix = 16
    chunk_size = 126
    c = [ord(b[i]) for i in range(d)]

    while len(c) % chunk_size != 0:
        c.append(0)

    # 分块加密
    encrypted_chunks = []
    for i in range(0, len(c), chunk_size):
        # 将块转换为一个大整数
        chunk = c[i:i + chunk_size]
        big_int = 0
        for j in range(len(chunk)):
            big_int += chunk[j] << (8 * j)  # 按位拼接

        # 模幂运算加密
        encrypted_chunk = pow(big_int, p, m)

        # 转换为字符串表示（按 radix）
        if radix == 16:
            encrypted_chunks.append(hex(encrypted_chunk)[2:].zfill(256))  # 去掉 "0x"
        else:
            encrypted_chunks.append(str(encrypted_chunk))

    # 用空格连接所有加密块
    return " ".join(encrypted_chunks)

def get_c(a: str) -> str:
    # 公钥指数
    public_exponent = "010001"
    # 模数
    modulus = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"

    b = int(public_exponent, 16)
    c = int(modulus, 16)
    result = encrypted_string(a, b, c)
    if len(result) < 256:
        result = result.zfill(256)  # 确保结果长度为 256 字节
    return result

def get_encrypt_data(text: str) -> Dict[str, str]:
    i = get_i(16)
    g = "0CoJUm6Qyw8W8jud"
    h = dict()
    h["params"] = get_b(get_b(text, g), i)
    h["encSecKey"] = get_c(i)
    return h