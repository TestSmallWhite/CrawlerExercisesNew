#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests

"""
输入17k小说网其中一部小说的章节网址，会自动下载所有的章节，并保存到本地

示例：
    《我爸是首富》章节网址：http://www.17k.com/list/2890059.html
"""

class autoDownloadText(object):
    # 章节网址列表
    global superLinkList
    superLinkList = []

    # 章节名列表
    global chaptersName
    chaptersName = []

    #获取每章小说链接
    def getTextList(self, url):
        global superLinkList

        global chaptersName

        #server用来拼接网址
        server = 'http://www.17k.com'

        #url是手动输入的小说章节网址，例如：http://www.17k.com/list/2890059.html
        req = requests.get(url = url)

        req.encoding = 'utf-8'

        #获取html源码
        req = req.text

        #features=表示beautifulsoup使用什么解释器去解析网页，最好指定，虽然不会出错，但是会有警告（看着也不爽）
        #这一步表示使用beautifulsouo去解析html，并获取beautifulsoup的对象
        bf = BeautifulSoup(req, features="html.parser")

        #找出所有指定标签底下的数据，这里要找的是dl标签（列表标签）class=“volume”下的所有数据
        dl_tagData = bf.find('dl', class_ = 'Volume')

        #上一步只拿到dl标签的数据，还需要再拿一次“a”标签的数据
        a_tagData = BeautifulSoup(str(dl_tagData),features="html.parser")

        a_tagData2 = a_tagData.find_all('a')

        #循环拿到每个章节的url
        for link in a_tagData2:

            #排除不需要的数据
            if link.get('href') == 'javascript:':
                pass
            else:
                #拼接每个章节的url
                superLink = server + link.get('href')

                #存到list中，方便等下调用
                superLinkList.append(superLink)

        #循环拿到每个章节的标题
        for link1 in a_tagData2:

            name = BeautifulSoup(str(link1),features="html.parser")

            s_name = name.find_all('span')

            for b in s_name:
                string = b.string.replace(' ', '').replace('\n', '')
                chaptersName.append(string)

    #根据每章小说的链接获取文本
    def getText(self,url):
        #发起请求
        req = requests.get(url=url)

        #改一下编码格式
        req.encoding = 'utf-8'

        #通过beautifulsoup筛选数据
        bf_data = BeautifulSoup(req.text, features='html.parser')

        #通过find_all找到文本
        data = bf_data.find_all('div', class_='p')

        #通过text（）把不相关的数据过滤掉
        text = data[0].text

        #去掉文本中的空格
        text = ''.join(text.split())

        #换行，因为是通过句号换行的，所以还是有问题，技术不精，无法在上一步中通过两个空格（看起来是像空格，无法确定）实现换行，不然格式就是网站上一样
        text = text.replace('。', '。\n')

        #加上两个换行符
        text = text + '\n\n'

        #把text返回出去
        return text

    #写入本地文件
    def copyAndWrite(self, path):
        with open(path, 'w',encoding='utf-8') as file:
            for x, y in zip(superLinkList, chaptersName):
                textData = self.getText(x)

                file.write(y + '    ' + x + '\n')

                file.write(textData)

        print("download ok!")







if __name__ == '__main__':
    #输入小说章节列表网址
    url = input("请输入网址:")

    #输入本地存储路径
    path = input("请输入存储的路径:")

    ob = autoDownloadText()

    print("开始获取文章链接")
    ob.getTextList(url)
    print("获取文章链接结束")

    print("开始写入文本")
    ob.copyAndWrite(path)
    print("写入文本结束")




