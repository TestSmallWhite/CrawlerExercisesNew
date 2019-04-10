import asyncio, async_timeout, time, re, json, os
import aiohttp
from bs4 import BeautifulSoup
from asyncio.locks import Lock


#用于存放变量的list,downLoadCountNow（当前下载的数量），NoPicAnswer（没有图片的回答），nimingCount（匿名回答数）,zhiHuUsers（重复的知乎用户）
variableList = [0,0,0,0]

#找出json中content的图片
findPicUrl = re.compile(r"https://pic\d\.zhimg\.com/v\d-.{32}_.{1,2}\.jpg")

#找出url的大小控制字符
findSize = re.compile(r"_.{1,2}\.jpg")

#获取锁
lock = Lock()

def checkStr(str):
    """
    检查昵称是否包含windows不合法的命名字符，如果找到就用"_"代替
    :param str: 回答者的昵称
    :return: 过滤后的昵称
    """
    return re.sub(r"[\/\\\:\*\?\"\<\>\|]", "_", str)

async def DownLoadPic(session, qestionSavePath, offset, questionId, downLoadCount):
    """
    :param session: 建立好的链接
    :param qestionSavePath: 问题保存路径
    :param offset: 知乎api的offset
    :param questionId: 问题id
    :param downLoadCount: 下载数量
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
    with async_timeout.timeout(10):
        async with session.get(urlAhead + str(offset) + urlBehind, proxy="http://proxy.tencent.com:8080") as response:
            #response.text() 返回的是协程对象，所以要转换下类型
            jsonData = str(await  response.text())

    #把json数据变成dict
    dictData = json.loads(jsonData)

    for x in range(dictData["data"].__len__()):
        #判断一下是否够下载数量了，acquire()需要加上“await”
        await lock.acquire()
        #downLoadCountNow（当前下载的数量），NoPicAnswer（没有图片的回答），nimingCount（匿名回答数）
        if variableList[0] == downLoadCount:
            print("已经够下载数量了")
            #release() 不需要加“await”
            lock.release()
            break
        else:
            variableList[0] += int(1)
            lock.release()

        #找出这个回答的图片
        picUrl = findPicUrl.findall(dictData["data"][x]["content"])

        #如果这个回答没有图片那么就跳过
        if picUrl.__len__() == 0:
            await lock.acquire()
            print("有一个没有图片哦：{}".format(checkStr(dictData["data"][x]["author"]["name"])))
            variableList[1] += int(1)
            lock.release()
            continue

        #拿到用户名并过滤
        answerName = checkStr(dictData["data"][x]["author"]["name"])

        if answerName == "匿名用户":
            await lock.acquire()
            print("一个匿名用户哦")
            answerName = answerName + str(variableList[2])
            variableList[2] += int(1)
            lock.release()

        #创建以用户名作为名字的文件夹
        nameSavePath = qestionSavePath +"\\" + str(answerName)
        if os.path.exists(nameSavePath):
            if answerName == "知乎用户":
                await lock.acquire()
                nameSavePath = qestionSavePath + "\\" + str(answerName) + variableList[3]
                variableList[3] += 1
                lock.release()
                os.makedirs(nameSavePath)
                print("一个知乎用户")
            else:
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
        with async_timeout.timeout(10):
            with open(nameSavePath + "\头像.jpg", "wb") as f:
                headPicUrl = re.sub(findSize, ".jpg", dictData["data"][x]["author"]["avatar_url"])
                async with session.get(headPicUrl, proxy="http://proxy.tencent.com:8080") as response:
                    #read()可以返回二进制的数据，text()不行
                    f.write(await response.read())

        #有些图片url是重复的，过滤一下
        temp = set()

        #下载图片
        for url in picUrl:
            #过滤一下控制大小的字符
            after_url = re.sub(findSize, ".jpg", url)

            if after_url in temp:
                continue

            temp.add(after_url)

            with async_timeout.timeout(10):
                with open(nameSavePath + "\\" + str(int(time.time())) + ".jpg", "wb" ) as f:
                    async with session.get(after_url,proxy="http://proxy.tencent.com:8080") as response:
                        f.write(await response.read())

            await asyncio.sleep(0.5)

        print("下载完毕一个回答:{}".format(answerName))

async def getQuestionAnswerCount(questionUrl, session):
    async with session.get(questionUrl, proxy="http://proxy.tencent.com:8080") as response:
        bf = BeautifulSoup(str(await response.text()), features="html.parser").find("h4", class_="List-headerText")
        return int(re.match(r".*<span>(\d*)<!.*", str(bf)).group(1))

async def main():
    startTime = time.time()
    async with aiohttp.ClientSession() as session:
        questionUrl = input("问题url是：")
        # questionUrl = "https://www.zhihu.com/question/274638737"

        answerCount = None
        answerCount = await getQuestionAnswerCount(questionUrl, session)
        # print(answerCount)

        savePath = input("请问保存地址是：")
        # savePath = "F:\\"

        downLoadCount = int(input("请问下载的数量是："))
        # downLoadCount = int(21)

        # 如果还没有拿到回答数，表示网络很差超时了，就结束程序
        if answerCount == None:
            await asyncio.sleep(5)

            # 等待5秒后，还是为None，就提示超时
            if answerCount == None:
                print("网络超时，结束程序")
                os.exit()

        # 判断下载数量是否大于回答数
        if downLoadCount > answerCount:
            print("该问题回答数为：{}".format(answerCount))
            print("下载数量大于问题回答数量，程序结束")
            os.exit()
        else:
            # 判断下载数量是否为零，零表示下载全部
            if downLoadCount == 0:
                downLoadCount = answerCount

            # 判断循环多少次
            if downLoadCount % 20 > 0:
                xunhuan = int(downLoadCount / 20) + 1
            else:
                xunhuan = downLoadCount / 20

            # 拿到问题的id
            questionId = re.match(r"https://www.zhihu.com/question/(\d*)", questionUrl).group(1)

            # 创建问题文件夹
            qestionSavePath = savePath + str(questionId)
            if os.path.exists(qestionSavePath):
                raise "这个文件夹已经存在了"
            else:
                os.makedirs(qestionSavePath)

                # 文件夹创建好了就可以启动协程了
                offset = -20
                tasks = []
                for x in range(0, xunhuan):
                    offset += 20
                    tasks.append(DownLoadPic(session, qestionSavePath, offset, questionId, downLoadCount))

                await asyncio.wait(tasks)
    print("耗时:{}".format(time.time() - startTime))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())
