from botoy import bot

# @bot.group_context_use
# def group_ctx_middleware(ctx: GroupMsg):
#     ctx.type = "group"  # 群聊
#     ctx.QQ = ctx.FromUserId  # 这条消息的发送者
#     ctx.QQG = ctx.FromGroupId  # 这条消息的QQ群
#     if ctx.MsgType == "AtMsg":  # @消息
#         ctx.AtContentDict = json.loads(ctx.Content)
#         ctx.AtUserID = ctx.AtContentDict["UserID"]
#         ctx.AtTips = ctx.AtContentDict.get("Tips")  # 回复消息时才有
#         ctx.AtContent = ctx.AtContentDict["Content"]
#     return ctx
#
#
# @bot.friend_context_use
# def friend_ctx_middleware(ctx: FriendMsg):
#     ctx.QQ = ctx.FromUin  # 这条消息的发送者
#     if ctx.MsgType == "TempSessionMsg":  # 临时会话
#         ctx.Content = json.loads(ctx.Content)["Content"]
#         ctx.type = "temp"
#         ctx.QQG = ctx.TempUin
#     else:
#         ctx.type = "friend"  # 好友会话
#         ctx.QQG = 0
#     return ctx


if __name__ == "__main__":
    bot.load_plugins()  # 加载插件
    bot.print_receivers()  # 打印插件信息
    bot.run()  # 一键启动
