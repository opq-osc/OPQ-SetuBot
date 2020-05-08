# [IOTBOT](https://github.com/IOTQQ/IOTQQ)的色图姬插件

在文件里填上bot的qq号和对应webapi地址和[key](https://api.lolicon.app/)运行就好了

文件里用了两个api,第一个是我[自己的](http://api.yuban10703.xyz:2333/setu),第二个是https://api.lolicon.app/#/

色图姬运行模式大概是这样:

![img](https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509060759.png)

关键字用了正则`r'来[点丶张](.*?)的{0,1}[色涩]图'`

![](https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509062823.png)

效果图(群聊或者私聊,@不行)[群聊:R18=False,私聊:R18=True]:

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509062130.jpg" alt="IMG_20200509_062059" style="zoom: 33%;" />

还有系统信息,发送==sysinfo==就行了(私聊或者群聊都可以,@不行)

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509061522.jpg" alt="IMG_20200509_061421" style="zoom: 33%;" />

还有[祖安模式](http://shadiao.app/)... 对bot说nmsl就行了(需要@,或者私聊)

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509061742.jpg" alt="IMG_20200509_061659" style="zoom:33%;" />

还有关于api的:

api地址http://api.yuban10703.xyz:2333/setu

色图仓库:https://github.com/laosepi/setu (每天3点自动从我的收藏夹更新色图)

请求方式:get

可选参数:

1. `tag`:P站的tag,str变量
2. `r18`:布尔变量,True或False

返回值的处理的话可以看插件的对应函数.....

图片url就是用返回值里面的filename和https://cdn.jsdelivr.net/gh/laosepi/setu/pics  拼接的