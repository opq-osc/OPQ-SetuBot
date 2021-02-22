import configparser

conf = configparser.ConfigParser()
conf.read('./config.ini', encoding="utf-8")

# bot
botqq = int(conf['bot']['qq'])
host = str(conf['bot']['host'])
port = int(conf['bot']['port'])
superadmin = int(conf['bot']['superadmin'])
# setu
api_pixiv = bool(int(conf['setu']['api_pixiv']))
api_yuban10703 = bool(int(conf['setu']['api_yuban10703']))
api_lolicon = bool(int(conf['setu']['api_lolicon']))
proxy = bool(int(conf['setu']['proxy']))
# # pixiv
# pixivUsername = str(conf['pixiv']['username'])
# pixivPassword = str(conf['pixiv']['password'])
# loliconApi
loliconApiKey: str = conf['loliconApi']['apiKey']
# saucenaoApi
saucenaoApiKey: str = conf['saucenaoApi']['apiKey']
