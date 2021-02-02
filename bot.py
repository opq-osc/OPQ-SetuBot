from botoy import Action, Botoy, GroupMsg, FriendMsg
from botoy import decorators as deco
from module import config, database
import json

bot = Botoy(qq=config.botqq,
            host=config.host,
            port=config.port,
            # log=True,
            log=False,
            use_plugins=True)

action = Action(qq=config.botqq, host=config.host, port=config.port)


@bot.group_context_use
def group_ctx_middleware(ctx: GroupMsg):
    ctx.type = 'group'  # 群聊
    ctx.QQ = ctx.FromUserId  # 这条消息的发送者
    ctx.QQG = ctx.FromGroupId  # 这条消息的QQ群
    ctx.accessLevel = database.BasicOperation.auth(ctx.QQG, ctx.QQ)  # 权限等级
    if ctx.MsgType == 'AtMsg':  # @消息
        ctx.AtContentDict = json.loads(ctx.Content)
        ctx.AtUserID = ctx.AtContentDict['UserID']
        ctx.AtTips = ctx.AtContentDict.get('Tips')  # 回复消息时才有
        ctx.Content = ctx.AtContentDict['Content']
    return ctx


@bot.friend_context_use
def friend_ctx_middleware(ctx: FriendMsg):
    ctx.QQ = ctx.FromUin  # 这条消息的发送者
    if ctx.MsgType == 'TempSessionMsg':  # 临时会话
        ctx.type = 'temp'
        ctx.QQG = ctx.TempUin
    else:
        ctx.type = 'friend'  # 好友会话
        ctx.QQG = 0
    ctx.accessLevel = database.BasicOperation.auth(ctx.QQG, ctx.QQ)
    return ctx


@bot.on_group_msg
@deco.queued_up(name="manage_plugin")
def manage_plugin(ctx: GroupMsg):
    if ctx.accessLevel != 1:
        return
    # action = Action(ctx.CurrentQQ)
    c = ctx.Content
    if c == "插件管理":
        action.sendGroupText(
            ctx.FromGroupId,
            (
                "py插件 => 发送启用插件列表\n"
                "已停用py插件 => 发送停用插件列表\n"
                "刷新py插件 => 刷新所有插件,包括新建文件\n"
                "重载py插件+插件名 => 重载指定插件\n"
                "停用py插件+插件名 => 停用指定插件\n"
                "启用py插件+插件名 => 启用指定插件\n"
            ),
        )
        return
    # 发送启用插件列表
    if c == "py插件":
        action.sendGroupText(ctx.FromGroupId, "\n".join(bot.plugins))
        return
    # 发送停用插件列表
    if c == "已停用py插件":
        action.sendGroupText(ctx.FromGroupId, "\n".join(bot.removed_plugins))
        return
    try:
        if c == "刷新py插件":
            bot.reload_plugins()
        # 重载指定插件 重载py插件+[插件名]
        elif c.startswith("重载py插件"):
            plugin_name = c[6:]
            bot.reload_plugin(plugin_name)
        # 停用指定插件 停用py插件+[插件名]
        elif c.startswith("停用py插件"):
            plugin_name = c[6:]
            bot.remove_plugin(plugin_name)
        # 启用指定插件 启用py插件+[插件名]
        elif c.startswith("启用py插件"):
            plugin_name = c[6:]
            bot.recover_plugin(plugin_name)
    except Exception as e:
        action.sendGroupText(ctx.FromGroupId, "操作失败: %s" % e)


if __name__ == "__main__":
    database.Getdata().updateAllGroupData()
    bot.run()
