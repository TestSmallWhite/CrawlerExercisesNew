# !/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
知乎爬虫改造，从单线程改成协程版本

思路：
    aiohttp 和 asyncio 搭配使用
    asyncio用来创建协程，aiohttp实现请求异步

拆分：
    把某些步骤拆分成可以异步协程的：
        下载图片
        获取json数据
        从json数据中找到下载地址，并存入到数组中

改造：
    v1.0的版本中，逻辑有点问题，现在改造一下
        当用户输入数量后，去获取最大回答数，然后判断
            输入0，表示下载全部回答

            当回答数满足下载数量，直接do it

            不满足就再次询问用户下载数量
                输入0，表示下载全部回答
                输入大于回答数量就继续询问
                输入小于回答数量就do it

        由于改成异步了，所以只显示完成某个回答下载，不再显示下载开始之类的

        显示整个下载过程的耗时，和单线程的对比，看下载速度快了多少

流程：
    1.先询问用户目标问题url
        异步去查询该问题最大回答数
    2.询问下载数量，用户输入数量
        输入0，表示下载全部，不用管异步的问题了

        输入一个整数
            这时需要考虑网络堵塞的问题，可能没有及时拿到回答数

            拿到回答数就开始判断

            没拿到就先跳过，等拿到太判断

    3.输入保存地址
        网络堵塞
            ！这时看下最大回答数拿到没？如果还是没拿到就看下哪个环节出问题了，然后在控制台打印错误，结束程序

        网络正常
            上一步已经开始下载工作了，这时还缺一个保存地址，当没输入地址，下载那块就先hold住（下载速度太快了，没有来得及输入地址）
            等地址就位了，才开始创建文件夹，保存文件



"""


import re, requests,json,os, time, sys, io
from bs4 import BeautifulSoup

proxies = {"http": "http://proxy.tencent.com:8080",
            "https": "http://proxy.tencent.com:8080"}

headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"
}

class coroutineVersion(object):
    def getAnswerCount(self, questionUrl):
        pass

if __name__ == '__main__':
    con = coroutineVersion()

    questionUrl = input("请输入知乎问题的url:")
    con.getAnswerCount(questionUrl)