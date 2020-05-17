# [IOTBOT](https://github.com/IOTQQ/IOTQQ)的色图姬插件

在文件里填上bot的qq号和对应webapi地址和[key](https://api.lolicon.app/)运行就好了

path是针对我的api的,会根据api返回的filename去path对应的路径找图,然后转换成base64发送,可以省下下载的时间..

色图仓库:https://github.com/laosepi/setu (每天3点自动从我的收藏夹更新色图)

文件里用了两个api,第一个是我[自己的](http://api.yuban10703.xyz:2333/setu),第二个是https://api.lolicon.app/#/

色图姬运行模式大概是这样:(去掉了在5分钟内发送过的功能......,懒得换图)

![img](https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509060759.png)

关键字用了正则`r'来(.*?)[点丶份张](.*?)的{0,1}[色瑟涩]图'`

![批注 2020-05-17 054642](https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200517054656.png)

效果图(群聊或者私聊,@不行)[群聊:R18=False,私聊:R18=True]:

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509062130.jpg" alt="IMG_20200509_062059" style="zoom: 33%;" />

还有系统信息,发送*sysinfo*就行了(私聊或者群聊都可以,@不行)

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509061522.jpg" alt="IMG_20200509_061421" style="zoom: 33%;" />

还有[祖安模式](http://shadiao.app/)... 对bot说*nmsl*就行了(需要@,或者私聊)

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509061742.jpg" alt="IMG_20200509_061659" style="zoom:33%;" />

还有关于api的:

api地址http://api.yuban10703.xyz:2333/setu_v2

请求方式:get

可选参数:

1. `tag`:P站的tag,str变量(不加tag就随机返回)
2. `num`:数量,int变量(最大10,默认1)
3. `r18`:布尔变量,True或False(默认False)[r18的判断是用腾讯ai的鉴黄接口判断的]

返回值:

| 字段名        | 数据类型 | 说明                                                     |
| ------------- | -------- | -------------------------------------------------------- |
| code          | int      | 200为正常,404表示图库中没有,500表示炸了,和http状态码一样 |
| title         | str      | 插画标题                                                 |
| artwork       | int      | 插画id                                                   |
| author        | str      | 作者名字                                                 |
| artist        | int      | 作者id                                                   |
| page          | str      | 插画的分p                                                |
| tags          | array    | p站的tag                                                 |
| filename      | str      | 文件名,用来拼凑url,或者本地转base64用                    |
| original      | str      | p站链接                                                  |
| large         | str      | p站链接                                                  |
| medium        | str      | p站链接                                                  |
| square_medium | str      | p站链接                                                  |

返回值的处理的话可以看插件的对应函数(setuapi_0).....

api的代码在https://github.com/yuban10703/Pixiv_download_to_mongodb/blob/master/api.py

图片url就是用返回值里面的filename和https://cdn.jsdelivr.net/gh/laosepi/setu/pics  拼接的

### 感谢

[lolicon](https://api.lolicon.app/#/setu)

[mcoo/iotqq-plugins-demo](https://github.com/mcoo/iotqq-plugins-demo)



