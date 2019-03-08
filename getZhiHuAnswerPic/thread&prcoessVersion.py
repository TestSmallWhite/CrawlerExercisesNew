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
import requests, re, os, time, json,sys
from bs4 import BeautifulSoup
import multiprocessing
from multiprocessing import Process,RLock

# 设置代理
proxies = {"http": "http://proxy.tencent.com:8080",
           "https": "http://proxy.tencent.com:8080"}

# 请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"
}

#找出json中content的图片
findPicUrl = re.compile(r"https://pic\d\.zhimg\.com/v\d-.{32}_.{1,2}\.jpg")

#找出url的大小控制字符
findSize = re.compile(r"_.{1,2}\.jpg")

#过滤掉用户名中含有不符合windows命名规则的字符
def checkStr(str):
    """
    检查昵称是否包含windows不合法的命名字符，如果找到就用"_"代替
    :param str: 回答者的昵称
    :return: 过滤后的昵称
    """
    return re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", str)

def getQuestionAnswerCount(questionUrl):
    """
        获取该问题回答数
        questionUrl：问题的url地址
        :return: 返回该问题回答数
    """
    req = requests.get(url=questionUrl, proxies=proxies, headers=headers).text
    #req = requests.get(url=self.questionURL, headers=headers).text

    bf = BeautifulSoup(req, features="html.parser").find("h4", class_="List-headerText")

    return int(re.match(r".*<span>(\d*)<!.*", str(bf)).group(1))


def getOffset(xunhuan):
    """
    生成器方法，返回接口的offset，用于获取数据
    :param xunhuan: 用于控制启动进程
    :return: None
    """
    n = 0
    offset = 0

    while True:
        if n > xunhuan:
            break
        else:
            yield offset
            n += 1
            offset += 20

def processDownLoadPic(mult_list, rLock, qestionSavePath, offset, questionId, downLoadCount):
    """
    进程下载图片方法
    :param mult_list: 同于进程同步的list，里面获取获取一些计数
    :param que: 用于进程同步的queue
    :param savePath: 保存地址
    :param of: 知乎接口中的offset值
    :return: None
    """


    #接口前半部分
    urlAhead = "https://www.zhihu.com/api/v4/questions/" + questionId + "/answers?include=data%5B%2A%5D.is_normal%" \
                "2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_" \
                "reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditabl" \
                "e_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time" \
                 "%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvot" \
                "ing%2Cis_thanked%2Cis_nothelp%2Cis_labeled%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A" \
                "%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit=20&offset="

    #接口后半部分
    urlBehind = "&platform=desktop&sort_by=default"

    #获取接口返回的json数据
    jsonData = requests.get(url=urlAhead + str(offset) + urlBehind, proxies=proxies, headers=headers).text

    #把json数据变成dict
    dictData = json.loads(jsonData)

    for x in range(dictData["data"].__len__()):
        #判断一下是否够下载数量了
        rLock.acquire()
        #downLoadCountNow（当前下载的数量），NoPicAnswer（没有图片的回答），nimingCount（匿名回答数）
        if mult_list[0] == downLoadCount:
            print("已经够下载数量了")
            rLock.release()
            break
        else:
            mult_list[0] += int(1)
            rLock.release()

        #找出这个回答的图片
        picUrl = findPicUrl.findall(dictData["data"][x]["content"])

        #如果这个回答没有图片那么就跳过
        if picUrl.__len__() == 0:
            rLock.acquire()
            print("有一个没有图片哦")
            mult_list[1] += int(1)
            rLock.release()
            continue

        #拿到用户名并过滤
        answerName = checkStr(dictData["data"][x]["author"]["name"])

        if answerName == "匿名用户":
            rLock.acquire()
            print("一个匿名用户哦")
            answerName = answerName + str(mult_list[2])
            mult_list[2] += int(1)
            rLock.release()

        #创建以用户名作为名字的文件夹
        nameSavePath = qestionSavePath +"\\" + str(answerName)
        if os.path.exists(nameSavePath):
            print(str(answerName) + " 文件夹已存在")
            continue
        else:
            os.makedirs(nameSavePath)

        #保存用户信息
        with open(nameSavePath + "\回答者信息.txt", "w+") as f:
            f.write(
                "id : " + dictData["data"][x]["author"]["id"] + "\n" +
                "简介 : " + dictData["data"][x]["author"]["headline"].replace("\n", "") + "\n" +
                # 其实知乎分好几种账号类型，people是普通用户，org是官方机构账号，这里就不再一一区分了，反正都能跳转
                # 详情页的真实格式：https://www.zhihu.com/user_type/url_token/activities
                "详情页 : https://www.zhihu.com/people/" + dictData["data"][x]["author"]["id"] + "\n" +
                "url_token : " + dictData["data"][x]["author"]["url_token"] + "\n" +
                "user_type : " + dictData["data"][x]["author"]["user_type"] + "\n" +
                "gender : " + str(dictData["data"][x]["author"]["gender"])
            )

        #下载头像
        with open(nameSavePath + "\头像.jpg", "wb") as f:
            headPicUrl = re.sub(findSize, ".jpg", dictData["data"][x]["author"]["avatar_url"])
            f.write(requests.get(url=headPicUrl, proxies=proxies, headers=headers).content)
            # f.write(requests.get(url=headPicUrl, headers=headers).content)

        #有些图片url是重复的，过滤一下
        temp = []

        #下载图片
        for url in picUrl:
            #过滤一下控制大小的字符
            after_url = re.sub(findSize, ".jpg", url)

            #continue只能跳出判断是否重复的for循环，由于python不支持跳出多重循环，所以设置一个变量
            flag = False

            for x in temp:
                if x == after_url:
                    flag = True
                    break

            if flag == True:
                continue

            temp.append(after_url)

            with open(nameSavePath + "\\" + str(int(time.time())) + ".jpg", "wb" ) as f:
                f.write(requests.get(url=after_url, proxies=proxies, headers=headers).content)

            time.sleep(2)

        with open(nameSavePath + "\下载url.txt", "w+") as f:
            #print(temp)
            for y in temp:
                f.write(y + "\n")

        print("下载完毕一个回答")

if __name__ == '__main__':
    questionUrl = input("问题url是：")
    # questionU = "https://www.zhihu.com/question/274638737"
    answerCount = getQuestionAnswerCount(questionUrl)
    #print(answerCount)

    savePath = input("请问保存地址是：")
    #savePath = "F:\\"

    downLoadCount = int(input("请问下载的数量是："))
    # downLoadCount = int(20)

    #判断下载数量是否大于回答数
    if downLoadCount > answerCount:
        print("下载数量大于问题回答数量，程序结束")
        # 这里不能使用return，是因为这个main函数了
        sys.exit()
    else:
        #判断下载数量是否为零，零表示下载全部
        if downLoadCount == 0:
            downLoadCount = answerCount
        else:
            #进程同步Queue
            rLock = RLock()

            # 初始化list，downLoadCountNow（当前下载的数量），NoPicAnswer（没有图片的回答），nimingCount（匿名回答数）
            mult_list = multiprocessing.Array("i", [0,0,0])

            #判断循环多少次
            if downLoadCount % 20 > 0:
                xunhuan = int(downLoadCount / 20) + 1
            else:
                xunhuan = downLoadCount / 20

            offset = getOffset(xunhuan)

            # 先拿到问题的id
            questionId = re.match(r"https://www.zhihu.com/question/(\d*)", questionUrl).group(1)

            #创建问题文件夹
            qestionSavePath = savePath + str(questionId)
            if os.path.exists(qestionSavePath):
                raise "这个文件夹已经存在了"
            else:
                os.makedirs(qestionSavePath)

            processs =[]

            for of in offset:
                process = Process(target=processDownLoadPic,args=(mult_list, rLock, qestionSavePath, of, questionId, downLoadCount))
                time.sleep(2)
                process.start()

            for x in processs:
                x.join()







