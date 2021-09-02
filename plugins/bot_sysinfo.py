import datetime
import time

import cpuinfo
import psutil
from botoy import S
from botoy import async_decorators as deco
from botoy import logger

__doc__ = "发送sysinfo查看系统信息"


class Sysinfo:
    @staticmethod
    def get_cpu_info():
        info = cpuinfo.get_cpu_info()  # 获取CPU型号等
        cpu_count = psutil.cpu_count(logical=False)  # 1代表单核CPU，2代表双核CPU
        xc_count = psutil.cpu_count()  # 线程数，如双核四线程
        cpu_percent = round(  # cpu使用率
            psutil.cpu_percent(),  # type:ignore
            2,
        )
        try:
            model = info["hardware_raw"]  # 树莓派能用这个获取到具体型号
        except:
            try:
                model = info["brand_raw"]  # cpu型号(我笔记本能用这个获取到具体型号,而且没有hardware_raw字段)
            except:
                model = "null"
        try:  # 频率
            freq = info["hz_actual_friendly"]
        except:
            freq = "null"
        return (
            "CPU型号:{}\r\n"
            "频率:{}\r\n"
            "架构:{}\r\n"
            "核心数:{}\r\n"
            "线程数:{}\r\n"
            "负载:{}%".format(model, freq, info["arch"], cpu_count, xc_count, cpu_percent)
        )

    @staticmethod
    def get_memory_info():
        memory = psutil.virtual_memory()
        total_nc = round((float(memory.total) / 1024 / 1024 / 1024), 3)  # 总内存
        used_nc = round((float(memory.used) / 1024 / 1024 / 1024), 3)  # 已用内存
        available_nc = round((float(memory.available) / 1024 / 1024 / 1024), 3)  # 空闲内存
        percent_nc = memory.percent  # 内存使用率

        return (
            "总内存:{}G\r\n"
            "已用内存:{}G\r\n"
            "空闲内存:{}G\r\n"
            "内存使用率:{}%".format(total_nc, used_nc, available_nc, percent_nc)
        )

    @staticmethod
    def get_swap_info():
        swap = psutil.swap_memory()
        swap_total = round((float(swap.total) / 1024 / 1024 / 1024), 3)  # 总swap
        swap_used = round((float(swap.used) / 1024 / 1024 / 1024), 3)  # 已用swap
        swap_free = round((float(swap.free) / 1024 / 1024 / 1024), 3)  # 空闲swap
        swap_percent = swap.percent  # swap使用率
        return (
            "swap:{}G\r\n"
            "已用swap:{}G\r\n"
            "空闲swap:{}G\r\n"
            "swap使用率:{}%".format(swap_total, swap_used, swap_free, swap_percent)
        )

    @staticmethod
    def uptime():
        now = time.time()
        boot = psutil.boot_time()
        boottime = datetime.datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S")
        nowtime = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
        up_time = str(
            datetime.datetime.utcfromtimestamp(now).replace(microsecond=0)
            - datetime.datetime.utcfromtimestamp(boot).replace(microsecond=0)
        )
        return "开机时间:{}\r\n" "当前时间:{}\r\n" "已运行时间:{}".format(boottime, nowtime, up_time)

    @classmethod
    def allInfo(cls):
        logger.info("sysinfo")
        return (
            "{cpu}\r\n"
            "{star}\r\n"
            "{mem}\r\n"
            "{star}\r\n"
            "{swap}\r\n"
            "{star}\r\n"
            "{uptime}".format(
                cpu=cls.get_cpu_info(),
                mem=cls.get_memory_info(),
                swap=cls.get_swap_info(),
                uptime=cls.uptime(),
                star="*" * 20,
            )
        )


@deco.ignore_botself
@deco.equal_content("sysinfo")
async def receive_group_msg(_):
    await S.atext(Sysinfo.allInfo())


@deco.ignore_botself
@deco.equal_content("sysinfo")
async def receive_friend_msg(_):
    await S.atext(Sysinfo.allInfo())
