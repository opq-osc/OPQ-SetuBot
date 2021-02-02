from botoy import EventMsg
from botoy.refine import refine_group_admin_event_msg, refine_group_join_event_msg
# from botoy import decorators as deco
from module import database, config
from loguru import logger


def receive_events(ctx: EventMsg):
    if admin_info := refine_group_admin_event_msg(ctx):
        if data_raw := database.BasicOperation.getGroupConf(admin_info.GroupID):
            if admin_info.Flag == 1:  # 变成管理员
                logger.info('群:{} QQ:{}成为管理员'.format(admin_info.GroupID, admin_info.UserID))
                if admin_info.UserID in data_raw['managers']:  # 防止重叠
                    data_raw['managers'].remove(admin_info.UserID)
                data_raw['admins'].append(admin_info.UserID)
            else:
                logger.info('群:{} QQ:{}被取消管理员'.format(admin_info.GroupID, admin_info.UserID))
                try:
                    data_raw['admins'].remove(admin_info.UserID)
                except:  # 出错就说明群信息不正确,重新获取
                    logger.warning('从数据库删除管理员出错,尝试重新刷新群数据')
                    database.Getdata.updateGroupData(admin_info.GroupID)
                    return
            database.BasicOperation.updateGroupData(admin_info.GroupID, data_raw)
        else:  # 如果没数据就重新获取
            database.Getdata.updateGroupData(admin_info.GroupID)
    elif join_info := refine_group_join_event_msg(ctx):
        if join_info.UserID == config.botqq:
            logger.info('bot加入群{}'.format(join_info.FromUin))
            database.Getdata.updateGroupData(join_info.FromUin)
        else:
            logger.info('{}:{}加入群{}'.format(join_info.UserName, join_info.UserID, join_info.FromUin))
    elif ctx.MsgType == 'ON_EVENT_GROUP_JOIN_SUCC':
        logger.info('bot加入群{}'.format(ctx.FromUin))
        database.Getdata.updateGroupData(ctx.FromUin)
