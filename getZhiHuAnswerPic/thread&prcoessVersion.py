#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
这是多线程和多进程的知乎爬虫

使用的multiprocessing的pool（线程池），和concurrent.future（这是一个异步线程池）搭配使用

现在知乎好像最多只能返回20个回答了

根据下载量开启进程，20个回答一个进程，一个进程20个线程

进程在启动的时候就分配好url了，线程要注意同步的问题

流程：
    1.用户输入了问题url后，立刻去查询这个问题最大的回答数
    2.判断下载数量是否比最大回答数大：
        大：通知用户，做出修改或者退出
        小：正常开始
        0：表示全部下载
    3.下载数量 / 20（决定了需要启动进程的数量，但是进程数量不宜很多，使用进程池控制，进程池在达到指定数量后，只能回收一个进程后再释放一个进程指标）
    4.在进程函数中，调用接口返回回答的json数据，收到json数据后
    5.然后实现多线程方法
    6.在进程函数中调用多线程方法，创建20个线程去下载图片
        requests并不是异步的，需要找个替代方法，这次先不管了，还是使用线程去调用requests


"""
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import requests, re, os, time, json
from bs4 import BeautifulSoup
from threading import RLock

# 设置代理
proxies = {"http": "http://proxy.tencent.com:8080",
           "https": "http://proxy.tencent.com:8080"}

# 请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"
}

class zhiHuPic(object):
    # def __init__(self, questionURL=None, savePath=None, count=None):
    #     # self.questionURL = questionURL  #问题的url
    #     # self.savePath = savePath    #保存地址
    #     # self.count = count  #想下载的数据
    #     # self.answerCount = 0 #问题总回答数

    def getQuestionAnswerCount(self,questionURL):
        """
        获取该问题回答数
        :return: 返回该问题回答数
        """
        req = requests.get(url=questionURL, proxies=proxies, headers=headers).text
        #req = requests.get(url=questionUrl, headers=headers).text

        bf = BeautifulSoup(req, features="html.parser").find("h4", class_="List-headerText")

        return re.match(r".*<span>(\d*)<!.*", str(bf)).group(1)

    #定义一个生成器，返回offset
    def getOffset(self,xunhuan):
        n = 0
        xunhuanCount = 0

        while True:
            if xunhuanCount <= xunhuan:
                yield n
                n += 20
                xunhuanCount += 1
            else:
                break

    #进程启动线程下载
    def getPic(self, of, questionId ):
        pass

    #这个方法用于分配任务
    def assignDownLoad(self, offset, questionId):
        #按20一个进程分配
        pool = multiprocessing.Pool(os.cpu_count())

        for of in offset:
            pool.apply_async(self.getPic,(None, of, questionId))




if __name__ == '__main__':
    #初始化实例
    zh = zhiHuPic()

    #询问问题的url
    questionUrl = input("请输入问题的url：")

    # 查询最大回答数，看下怎么搞成异步的
    # 放弃了，还是直接撸吧，有问题就留到专门使用异步的框架解决
    questionCount = int(zh.getQuestionAnswerCount(questionUrl))

    #询问保存地址
    savePath = input("请输入保存图片的地址：")

    #询问下载数量
    #0表示全部下载
    #下载数量大于回答数就提示，小于就直接执行
    downLoadCount = int(input("请输入下载数量："))
    if downLoadCount > questionCount:
        print("问题最大回答数={}".format(questionCount))
        raise "超出了最大回答数，请重新运行"
    else:
        xuanhuan = 0

        #如果输入0表示全部下载
        if downLoadCount == 0:
            downLoadCount = questionCount

        #判断需要循环多少次，20一个循环
        if downLoadCount % 20 > 0:
            xunhuan = downLoadCount / 20 + 1
        else:
            xunhuan = downLoadCount / 20
        offset = zh.getOffset(xunhuan)
        questionId = re.match(r"https://www.zhihu.com/question/(\d*)", questionUrl).group(1)
        zh.assignDownLoad(offset, questionId)






