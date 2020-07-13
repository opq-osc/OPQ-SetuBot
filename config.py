import re,json

with open('config.json', 'r', encoding='utf-8') as f:  # 从json读配置
    config = json.loads(f.read())
    print('加载配置成功')

# configData = config
color_pickey = config['color_pickey']  # 申请地址api.lolicon.app
webapi = config['webapi']  # Webapi接口 http://127.0.0.1:8888
botqqs = config['botqqs']  # 机器人QQ号
setu_pattern = re.compile(config['setu_pattern'])  # 色图正则
setu_path = config['path']  # 色图路径
send_original_pic = config['send_original_pic']  # 是否发送原图
not_send_pic_info = config['not_send_pic_info']  # 是否只发图
setu_threshold = int(config['setu_threshold'])  # 发送上限
threshold_to_send = config['threshold_to_send']  # 超过上限后发送的文字
notfound_to_send = config['notfound_to_send']  # 没找到色图返回的文字
frequency_cap_to_send = config['frequency_cap_to_send']  # 达到频率上限后发送语句
wrong_input_to_send = config['wrong_input_to_send']  # 关键字错误返回的文字
before_nmsl_to_send = config['before_nmsl_to_send']  # 嘴臭之前发送的语句
Permission_denied_to_send = config['Permission_denied_to_send']  # 嘴臭之前发送的语句
before_setu_to_send_switch = config['before_setu_to_send_switch']  # 发色图之前是否发送消息
send_setu_at = config['send_setu_at']  # 发色图时是否@
before_setu_to_send = config['before_setu_to_send']  # 发色图之前的语句
group_blacklist = config['group_blacklist']
group_whitelist = config['group_whitelist']
group_r18_whitelist = config['group_r18_whitelist']
private_for_group_blacklist = config['private_for_group_blacklist']
private_for_group_whitelist = config['private_for_group_whitelist']
private_for_group_r18_whitelist = config['private_for_group_r18_whitelist']
RevokeMsg = config['RevokeMsg']
RevokeMsg_time = int(config['RevokeMsg_time'])
sentlist_switch = config['sentlist_switch']
good_morning = config['good_morning']
morning_keyword = config['morning_keyword']
good_night = config['good_night']
night_keyword = config['night_keyword']
morning_conf = config['morning_conf']
night_conf = config['night_conf']
morning_repeat = config['morning_repeat']
morning_num_msg = config['morning_num_msg']
night_repeat = config['night_repeat']
night_num_msg = config['night_num_msg']
superAdminQQ = config['superAdminQQ']
adminQQs = config['adminQQs']

frequency = config['frequency']
frequency_additional = config['frequency_additional']
reset_freq_time = config['reset_freq_time']

clear_sentlist_time = int(config['clear_sentlist_time'])