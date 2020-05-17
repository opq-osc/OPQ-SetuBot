import asyncio
import aiohttp
import base64
import json

from sex_pic import *
path = 'Y:\\PICS\\'


with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())
sent = []  # 记录发送过的id
color_pickey = config['color_pickey']  # 申请地址api.lolicon.app
size1200 = config['size1200']  # 是否使用 master_1200 缩略图，即长或宽最大为1200px的缩略图，以节省流量或提升加载速度（某些原图的大小可以达到十几MB）
webapi = config['webapi']  # Webapi接口 http://127.0.0.1:8888
robotqq = config['robotqq']  # 机器人QQ号
path = config['path']  # 色图路径

class Sysinfo():
    def get_cpu_info(self):
        info = cpuinfo.get_cpu_info()  # 获取CPU型号等
        cpu_count = psutil.cpu_count(logical=False)  # 1代表单核CPU，2代表双核CPU
        xc_count = psutil.cpu_count()  # 线程数，如双核四线程
        cpu_percent = round((psutil.cpu_percent()), 2)  # cpu使用率
        try:
            model = info['brand']
        except:
            model = info['hardware']
        try:
            freq = info['hz_actual']
        except:
            freq = 'null'
        cpu_info = (model, freq, info['arch'], cpu_count, xc_count, cpu_percent)
        return cpu_info

    def get_memory_info(self):
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        total_nc = round((float(memory.total) / 1024 / 1024 / 1024), 3)  # 总内存
        used_nc = round((float(memory.used) / 1024 / 1024 / 1024), 3)  # 已用内存
        available_nc = round((float(memory.available) / 1024 / 1024 / 1024), 3)  # 空闲内存
        percent_nc = memory.percent  # 内存使用率
        swap_total = round((float(swap.total) / 1024 / 1024 / 1024), 3)  # 总swap
        swap_used = round((float(swap.used) / 1024 / 1024 / 1024), 3)  # 已用swap
        swap_free = round((float(swap.free) / 1024 / 1024 / 1024), 3)  # 空闲swap
        swap_percent = swap.percent  # swap使用率
        men_info = (total_nc, used_nc, available_nc, percent_nc, swap_total, swap_used, swap_free, swap_percent)
        return men_info

    def uptime(self):
        now = time.time()
        boot = psutil.boot_time()
        boottime = datetime.datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")
        nowtime = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
        up_time = str(
            datetime.datetime.utcfromtimestamp(now).replace(microsecond=0) - datetime.datetime.utcfromtimestamp(
                boot).replace(microsecond=0))
        alltime = (boottime, nowtime, up_time)
        return alltime

    def get_sysinfo(self):
        cpu_info = self.get_cpu_info()
        mem_info = self.get_memory_info()
        up_time = self.uptime()
        msg = 'CPU型号:{0}\r\n频率:{1}\r\n架构:{2}\r\n核心数:{3}\r\n线程数:{4}\r\n负载:{5}%\r\n{6}\r\n' \
              '总内存:{7}G\r\n已用内存:{8}G\r\n空闲内存:{9}G\r\n内存使用率:{10}%\r\n{6}\r\n' \
              'swap:{11}G\r\n已用swap:{12}G\r\n空闲swap:{13}G\r\nswap使用率:{14}%\r\n{6}\r\n' \
              '开机时间:{15}\r\n当前时间:{16}\r\n已运行时间:{17}'
        full_meg = msg.format(cpu_info[0], cpu_info[1], cpu_info[2], cpu_info[3], cpu_info[4], cpu_info[5], '*' * 20,
                              mem_info[0], mem_info[1], mem_info[2], mem_info[3], mem_info[4],
                              mem_info[5], mem_info[6], mem_info[7], up_time[0], up_time[1], up_time[2])
        return full_meg


def pixiv_url(title, artworkid, author, artistid):  # 拼凑消息
    purl = "www.pixiv.net/artworks/" + str(artworkid)  # 拼凑p站链接
    uurl = "www.pixiv.net/users/" + str(artistid)  # 画师的p站链接
    msg = title + "\r\n" + purl + "\r\n" + author + "\r\n" + uurl
    return msg

def base_64(filename):
    with open(path + filename, 'rb') as f:
        coding = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
        print('本地base64转码~')
        return coding.decode()

async def setuapi_0(tag='', num=1, r18=0):
    # url = 'http://api.yuban10703.xyz:2333/setu'
    url = 'http://10.1.1.1:2333/setu_v2'
    params = {'r18': r18,
              'num': num,
              'tag': tag}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, timeout=5) as res:
                setu_data = await res.json()
    except:
        print('api_0,boom~~')
        return '', '', '请求出错啦~'
    if res.status == 200:
        title = setu_data['data'][0]['title']  # 标题
        author = setu_data['data'][0]['author']  # 作者
        artworkid = setu_data['data'][0]['artwork']
        artistid = setu_data['data'][0]['artist']
        filename = setu_data['data'][0]['filename']  # 文件名
        print('尝试从yubanのapi获取')

        if path == '':
            url = 'https://cdn.jsdelivr.net/gh/laosepi/setu/pics/' + filename
            base64_code = ''
        else:
            url = ''
            base64_code = base_64(filename)
        msg = pixiv_url(title, artworkid, author, artistid)
        return url, base64_code, msg
    return '', '', 'error'


async def setuapi_1(keyword='', r18=0):
    url = 'https://api.lolicon.app/setu/'
    params = {'r18': r18,
              'apikey': '113398405e98f340bbb5d6',
              'keyword': keyword,
              'size1200': size1200,
              'proxy': 'i.pixiv.cat'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params, timeout=5) as res:
                print(res.status)
                setu_data = await res.json()
                print(setu_data)
    except:
        print('api_1,boom~~')
        return '', '服务器爆炸啦~'
    print('尝试从lolicon获取')
    if setu_data['code'] == 404:
        return '', '你的xp好奇怪啊 爪巴'
    if setu_data['code'] == 429:
        return '', '没图了 爪巴'
    picurl = setu_data['data'][0]['url']  # 提取图片链接
    author = setu_data['data'][0]['author']  # 提取作者名字
    title = setu_data['data'][0]['title']  # 图片标题
    artworkid = setu_data['data'][0]['pid']
    artistid = setu_data['data'][0]['uid']
    msg = pixiv_url(title, artworkid, author, artistid)
    return picurl, msg


async def get_setu(keyword, r18=0):
    data = await setuapi_0(keyword, 1, r18)
    if data[0] != data[1]:
        # sent.append(data['_id'])
        return data[0], data[1], data[2]
    else:
        data_1 = await setuapi_1(keyword, r18)
        if data_1[0] != '':
            return data_1[0], '', data_1[1]
        else:
            return '', '', data_1[1]


async def nmsl():
    api = 'https://nmsl.shadiao.app/api.php?from=sunbelife'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=api, timeout=5) as res:
                await res.text()
    except:
        return '酝酿失败~'
    return res


if __name__ == '__main__':
    # asyncio.run(get_setu('a'))
    a = Sysinfo()
    n = a.get_sysinfo()
