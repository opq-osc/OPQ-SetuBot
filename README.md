# [IOTBOT](https://github.com/IOTQQ/IOTQQ)的色图姬插件

在config里填上bot的qq号和对应webapi地址和[key](https://api.lolicon.app/)运行就好了,那些黑名单 白名单什么的没特殊要求就不用管了....

| config                          | 数据类型 | 说明                                                         |
| ------------------------------- | -------- | ------------------------------------------------------------ |
| color_pickey                    | str      | lolicon的key                                                 |
| send_original_pic               | bool     | 是否发送原图                                                 |
| not_send_pic_info               | bool     | 是否不发送图片信息                                           |
| send_setu_at                    | bool     | 在发图时是否@                                                |
| webapi                          | str      | webapi的的地址                                               |
| botqqs                          | array    | bot的qq(支持多QQ)                                            |
| group_blacklist                 | array    | 群黑名单(加入后会无视这些群,与白名单二选一)  [如果黑名单和白名单都没数据就默认对所有群生效] |
| group_whitelist                 | array    | 群白名单(加入后只对里面的群生效,与黑名单二选一)              |
| group_r18_whitelist             | array    | 开启r18的群白名单(可以调用`来张r18色图`)                     |
| private_for_group_blacklist     | array    | 群临时会话黑名单,加入的群 临时会话不会发色图   (黑白名单二选一,不能都填) |
| private_for_group_whitelist     | array    | 群临时会话白名单,只有加入的群 临时会话才有用  (黑白名单二选一,不能都填) |
| private_for_group_r18_whitelist | array    | 开启r18的群的临时会话白名单(可以调用`来张r18色图`)           |
| setu_pattern                    | str      | 识别用的正则表达式                                           |
| path                            | str      | 本地图库的路径(本地没图空着就行),比如'/root/setu/PICS/',可以把色图仓库gitclone下来..... |
| setu_threshold                  | int      | 限制一次能要多少色图...(最大20)                              |
| frequency                       | int      | 发图的限制数量(设置0为不做限制)                              |
| reset_freq_time                 | int      | 重置frequency的倒计时(秒)----------(如果frequency设置20,reset_freq_time设置60,那就是60s内可以发20张图)   [设置0为不重置] |
| frequency_additional            | dict     | 额外的群,如果有些群需要单独设置限制频率就添加在这个里面( 比如123456群不做限制,654321群限制40:   "frequency_additional": {"123456":0,"654321":40}, ) |
| RevokeMsg                       | bool     | 是否撤回图片消息                                             |
| RevokeMsg_time                  | int      | 撤回倒计时(秒)                                               |
| sentlist_switch                 | bool     | 记录我api发送过的图片,在一段时间里不再发送                   |
| clear_sentlist_time             | int      | 重置我api发送过的图片的倒计时(秒)                            |
| threshold_to_send               | str      | 超过setu_threshold后发送的消息                               |
| notfound_to_send                | str      | 没找到色图时的消息                                           |
| wrong_input_to_send             | str      | 输入错误时的消息                                             |
| frequency_cap_to_send           | str      | 可以轻微自定义语句,里面的`{reset_freq_time},{frequency},{num},{refresh_time}`位置可以换,但不能没有 |
| before_nmsl_to_send             | str      | 嘴臭前的消息                                                 |
| before_setu_to_send_switch      | bool     | 是否在发色图之前发送消息                                     |
| before_setu_to_send             | str      | 在发色图前发送的消息                                         |
| frequency_cap_to_send           | str      | 当达到频率限制后发送的消息                                   |
| good_morning                    | bool     | 是否开启早安功能                                             |
| morning_keyword                 | array    | 触发早安的关键字                                             |
| morning_conf                    | dict     | 各个时间段的回复,可以修改or添加(按照格式往下添加就好了,时间段必须全部覆盖,24小时制)**[必须以00:00开始,00:00结束]** |
| morning_num_msg                 | str      | 可以自定义但是`{num}`不能少,`\r\n`是换行符                   |
| morning_repeat                  | str      | 重复触发的消息                                               |
| good_night                      | bool     | 是否开启晚安功能                                             |
| night_keyword                   | array    | 晚安关键字                                                   |
| night_conf                      | dict     | 各个时间段的回复,可以修改or添加(按照格式往下添加就好了,时间段必须全部覆盖,24小时制)**[必须以00:00开始,00:00结束]** |
| night_num_msg                   | str      | 可以自定义但是`{num}`不能少,`\r\n`是换行符                   |
| night_repeat                    | str      | 重复触发的消息                                               |



path是针对我的api的,会根据api返回的filename去path对应的路径找图,然后转换成base64发送,可以省下下载的时间..

色图仓库:https://github.com/laosepi/setu (每天4点自动从我的收藏夹更新色图)

文件里用了两个api,第一个是我[自己的](http://api.yuban10703.xyz:2333/docs),第二个是https://api.lolicon.app/#/



色图姬运行模式大概是这样:

![img](https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509060759.png)

关键字用了正则`来(.*?)[点丶份张幅](.*?)的?(|r18)[色瑟涩][图圖]`:

![image-20200704192100243](https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200704192100.png)

效果图(群聊或者私聊,@不行):

**ps:**

​	来张r18色图 :,r18:true

​	来张r18的色图,r18:false

​	来张r18的r18色图,r18:true

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509062130.jpg" alt="IMG_20200509_062059" style="zoom: 33%;" />

还有系统信息,发送*sysinfo*就行了(私聊或者群聊都可以,@不行):

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509061522.jpg" alt="IMG_20200509_061421" style="zoom: 33%;" />

还有[祖安模式](http://shadiao.app/)... 对bot说*nmsl*就行了(需要@,或者私聊):

<img src="https://cdn.jsdelivr.net/gh/yuban10703/BlogImgdata/img/20200509061742.jpg" alt="IMG_20200509_061659" style="zoom:33%;" />

还有关于api的:

api地址http://api.yuban10703.xyz:2333/setu_v3

请求方式:get

可选参数:

| 字段名 | 数据类型 | 说明                                                         |
| ------ | -------- | ------------------------------------------------------------ |
| tag    | str      | P站的tag(不加tag就随机返回)                                  |
| num    | int      | 数量(最大10,默认1)                                           |
| type   | int      | 0: 'normal', 1: 'sexy', 2: 'porn', 3: 'all'(腾讯ai + 我手动筛的) |

返回值:

| 字段名 | 数据类型 | 说明                                                     |
| ------ | -------- | -------------------------------------------------------- |
| code   | int      | 200为正常,404表示图库中没有,500表示炸了,和http状态码一样 |
| count  | int      | data内的数据数量                                         |
| data   | array    | setu列表                                                 |

data:

| 字段名        | 数据类型 | 说明                                  |
| ------------- | -------- | ------------------------------------- |
| title         | str      | 插画标题                              |
| artwork       | int      | 插画id                                |
| author        | str      | 作者名字                              |
| artist        | int      | 作者id                                |
| page          | int      | 插画的分p                             |
| tags          | array    | p站的tag                              |
|type           | str	   | 色图类型								|
| filename      | str      | 文件名,用来拼凑url,或者本地转base64用 |
| original      | str      | p站链接                               |
| large         | str      | p站链接                               |
| medium        | str      | p站链接                               |
| square_medium | str      | p站链接                               |
返回值的处理的话可以看插件的对应函数(setuapi_0).....

api的代码在https://github.com/yuban10703/Pixiv_download_to_mongodb

图片url就是用返回值里面的filename和https://cdn.jsdelivr.net/gh/laosepi/setu/pics  拼接的

### 感谢

[lolicon](https://api.lolicon.app/#/setu)

[沙雕APP](https://shadiao.app/)

[mcoo/iotqq-plugins-demo](https://github.com/mcoo/iotqq-plugins-demo)

[CQ-picfinder-robot](https://github.com/Tsuk1ko/CQ-picfinder-robot)

