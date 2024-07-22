from botoy import bot, scheduler, logger
import gc


def free_mem():
    gc.collect()
    logger.info("gc.collect()")


scheduler.add_job(
    free_mem,
    "cron",
    minute="*/5",
    # second="*/30",
    misfire_grace_time=10,
)  # 5分钟 gc一次

if __name__ == "__main__":
    bot.load_plugins()  # 加载插件
    bot.print_receivers()  # 打印插件信息
    bot.run()  # 一键启动
