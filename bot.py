import asyncio

import ujson as json
from botoy import AsyncBotoy, FriendMsg, GroupMsg, jconfig

bot = AsyncBotoy(
    qq=jconfig.qq,
    host=jconfig.host,
    port=jconfig.port,
    log=True,
    # log=False,
    log_file=True,
    use_plugins=True,
)


@bot.group_context_use
def group_ctx_middleware(ctx: GroupMsg):
    ctx.type = "group"  # 群聊
    ctx.QQ = ctx.FromUserId  # 这条消息的发送者
    ctx.QQG = ctx.FromGroupId  # 这条消息的QQ群
    if ctx.MsgType == "AtMsg":  # @消息
        ctx.AtContentDict = json.loads(ctx.Content)
        ctx.AtUserID = ctx.AtContentDict["UserID"]
        ctx.AtTips = ctx.AtContentDict.get("Tips")  # 回复消息时才有
        ctx.AtContent = ctx.AtContentDict["Content"]
    return ctx


@bot.friend_context_use
def friend_ctx_middleware(ctx: FriendMsg):
    ctx.QQ = ctx.FromUin  # 这条消息的发送者
    if ctx.MsgType == "TempSessionMsg":  # 临时会话
        ctx.Content = json.loads(ctx.Content)["Content"]
        ctx.type = "temp"
        ctx.QQG = ctx.TempUin
    else:
        ctx.type = "friend"  # 好友会话
        ctx.QQG = 0
    return ctx


if __name__ == "__main__":
    asyncio.run(bot.run())
