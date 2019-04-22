import json
import requests


class YDMHttp(object):
    apiurl = 'http://api.yundama.com/api.php'
    username = ''
    password = ''
    appid = ''
    appkey = ''

    def __init__(self, username, password, appid, appkey):
        self.username = username
        self.password = password
        self.appid = str(appid)
        self.appkey = appkey

    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey}
        response_data = requests.post(self.apiurl, data=data)
        ret_data = json.loads(response_data.text)
        if ret_data["ret"] == 0:
            print("剩余积分", ret_data["balance"])
            return ret_data["balance"]
        else:
            return None

    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey}
        response_data = requests.post(self.apiurl, data=data)
        ret_data = json.loads(response_data.text)
        if ret_data["ret"] == 0:
            print("登录成功", ret_data["uid"])
            return ret_data["uid"]
        else:
            return None

    def decode(self, filename, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        files = {'file': open(filename, 'rb')}
        response_data = requests.post(self.apiurl, files=files, data=data)
        ret_data = json.loads(response_data.text)
        if ret_data["ret"] == 0:
            return ret_data["text"]
        else:
            return "识别失败"


# if __name__ == "__main__":
#     # 用户名
#     username = 'hugol'
#     # 密码
#     password = 'lyg960926'
#     # 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
#     appid = 6681
#     # 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！
#     appkey = 'b2b32282d67bd432e56b08774b999481'
#     # 图片文件
#     filename = 'captcha.jpeg'
#     # 验证码类型，# 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
#     codetype = 5000
#     # 超时时间，秒
#     timeout = 30
#     # 检查
#     if username == 'username':
#         print('请设置好相关参数再测试')
#     else:
#         # 初始化
#         yundama = YDMHttp(username, password, appid, appkey)
#
#         # 登陆云打码
#         uid = yundama.login()
#
#         # 查询余额
#         balance = yundama.balance()
#
#         # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
#         text = yundama.decode(filename, codetype, timeout)
