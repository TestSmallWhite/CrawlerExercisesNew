#!usr/bin/env python3
# -*- coding:utf-8 -*-

"""
需求：
    输入某个知乎问题链接，自动爬回答的基本信息
    可以指定爬多少个回答
        需要判断是否超出问题的最大回答数
            超出，给出友好提示
            不超出，开始下载
    基本信息：
        头像  avatar_url）
            把用户头像url的"_**"删除，就是用户的原图啦
        昵称  name（用来做每个回答的文件夹名）
            ！！！由于windows的问题，需要过滤一下昵称中不合法的字符
            知乎可以匿名回答， 每个匿名回答，昵称都是“匿名用户”。需要对“匿名用户”特殊处理，把匿名回答的昵称改成“匿名用户” + 1（累加）
        id
        简介  headline
        主页url
            需要自己处理一下
            https://www.zhihu.com/people/ + 用户id
        用户的类型   user_type

        url_token

        图片 content中的img，src中的url被加上了\""\所以要匹配出来，然后删除
            同时还有一些其他资源的img，也应该把它过滤掉



接口：
    加载更多数据接口
    https://www.zhihu.com/api/v4/questions/301492431/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit=5&offset=55&platform=desktop&sort_by=default

"""

import re, requests,json,os, time
from bs4 import BeautifulSoup

proxies = {"http": "http://proxy.tencent.com:8080",
            "https": "http://proxy.tencent.com:8080"}

headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"
}

class getPic(object):
    def __init__(self, questionURL, savePath, count):
        self.questionURL = questionURL  #问题的url
        self.savePath = savePath    #保存地址
        self.count = count  #想下载的数据
        self.answerCount = 0 #问题总回答数，默认下载全部

    def getQuestionAnswerCount(self):
        """
        获取该问题回答数
        :return: 返回该问题回答数
        """
        req = requests.get(url=self.questionURL, proxies=proxies, headers=headers).text

        bf = BeautifulSoup(req, features="html.parser").find("h4", class_="List-headerText")

        self.answerCount =  re.match(r".*<span>(\d*)<!.*", str(bf)).group(1)

    def downloadAnswer(self):
        """
        下载回答者的信息
        :return:
        """

        #找出content中所有图片url的正则表达式
        findPicUrl = re.compile(r"https://pic\d\.zhimg\.com/v\d-.{32}_.{1,2}\.jpg")

        #找出图片url中控制分辨率的字符
        findSize = re.compile(r"_.{1,2}\.jpg")

        #看下该问题有多少个回答
        self.getQuestionAnswerCount()

        #先判断一下问题回答数是否大于目标下载数,不够提示使用者
        if int(self.answerCount) >= int(self.count):
            #知乎一次最大只返回10个回答，所以循环次数 = 下载数 / 10 + 1
            #如果self.count=0,表示下载全部回答
            if self.count == 0:
                xunhuanCount = int(self.answerCount / 10) + 1
            else:
                xunhuanCount = int(self.count / 10) + 1

            #位移数
            offset = 0

            #处理知乎api
            #先拿到问题的id
            questionId = re.match(r"https://www.zhihu.com/question/(\d*)", self.questionURL).group(1)

            urlAhead = "https://www.zhihu.com/api/v4/questions/" + questionId + "/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit=20&offset="
            urlBehind = "&platform=desktop&sort_by=default"

            #用来匿名回答数+1
            niMingCount = 0

            for num in range(0, xunhuanCount):

                dataJson = requests.get(url=urlAhead + str(offset) + urlBehind, proxies=proxies, headers=headers).text

                #把数据变成dict类型
                dataJson = json.loads(dataJson)

                for x in range(dataJson["data"].__len__()):
                    #过滤下content，如果没有图片就跳过
                    url = findPicUrl.findall(dataJson["data"][x]["content"])

                    if url.__len__() == 0:
                        continue

                    #拿到用户的name，过滤后用作文件夹的命名
                    name = self.checkStr(dataJson["data"][x]["author"]["name"])

                    #判断是不是匿名回答
                    if name == "匿名用户":
                        name = name + str(niMingCount)
                        niMingCount = niMingCount + 1

                    path = self.savePath + str(questionId) + "\\"  + name
                    #print(path)

                    #先创建文件夹
                    os.makedirs(path)

                    with open(path + "\回答者信息.txt", "w+") as f:
                        f.write(
                            "id : " + dataJson["data"][x]["author"]["id"] + "\n" +
                            "简介 : " + dataJson["data"][x]["author"]["headline"].replace("\n", "") + "\n" +
                            #其实知乎分好几种账号类型，people是普通用户，org是官方机构账号，这里就不再一一区分了，反正都能跳转
                            #详情页的真实格式：https://www.zhihu.com/user_type/url_token/activities
                            "详情页 : https://www.zhihu.com/people/" + dataJson["data"][x]["author"]["id"] + "\n" +
                            "url_token : " + dataJson["data"][x]["author"]["url_token"] + "\n" +
                            "user_type : " + dataJson["data"][x]["author"]["user_type"] + "\n" +
                            "gender : " + str(dataJson["data"][x]["author"]["gender"])
                        )

                    #下载头像
                    with open(path + "\头像.jpg", "wb") as f:
                        headPicUrl = re.sub(findSize, ".jpg", dataJson["data"][x]["author"]["avatar_url"])
                        f.write(requests.get(url=headPicUrl, proxies=proxies, headers=headers).content)

                    time.sleep(2)

                    # 发现有重复url的情况，存进数组里面，过滤一下
                    is_duplication = []

                    #下载图片了，图片用时间戳作为名字
                    for x in url:
                        #print(x)

                        #过滤一下url中的size字符
                        answerPicUrl = re.sub(findSize, ".jpg", x)
                        #print(answerPicUrl)

                        #因为python不支持跳出多重循环，所以设置一个变量控制
                        flag = False

                        for y in is_duplication:
                            if answerPicUrl == y:
                                flag = True
                                break

                        if flag:
                            continue

                        is_duplication.append(answerPicUrl)

                        with open(path + "\\" + str(int(time.time())) + ".jpg", "wb") as f:
                            f.write(requests.get(url=answerPicUrl, proxies=proxies, headers=headers).content)

                        time.sleep(2)

                print("下载完毕一个回答")
                is_duplication = []

                offset = offset + 10


        else:
            print("你想下载的数量超过了该问题最大回答数，该问题最大回答数为" + str(self.answerCount) + "个。")


    def checkStr(self, str):
        """
        检查昵称是否包含windows不合法的命名字符，如果找到就用"_"代替
        :param str: 回答者的昵称
        :return: 过滤后的昵称
        """
        return re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", str)

if __name__ == '__main__':
    gb = getPic("https://www.zhihu.com/question/26297181", "f:\\",5)
    gb.downloadAnswer()
    print("下载完毕")


