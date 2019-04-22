import re
import datetime
import hashlib
import requests
import tesserocr
from PIL import Image
from tools.yundama_requests.yundama_requests import YDMHttp
from tools.zheye import zheye
from pymongo.collection import Collection
import pymongo


# 对字符串做哈希运算，得出md5值
def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5(url)
    return m.hexdigest()


# 提取字符串中的数字并返回
def extract_num(value):
    re_num = re.match(r".*?(\d+).*", value)
    if re_num:
        num = int(re_num.group(1))
    else:
        num = 0
    return num


# 时间转换，否则输出当前北京时间
def date_convert(value):
    try:
        date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        print(e)
        date = datetime.datetime.now().date()
    return date


# 通过OCR识别图片中的验证码，识别率较低
def get_captcha():
    image = Image.open("1.jpg")
    image = image.convert('L')
    threshold = 220
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)
        else:
            table.append(1)
    image = image.point(table, '1')
    result = tesserocr.image_to_text(image)
    print(result)


# 通过付费打码平台第三方接口对验证码进行识别并返回，识别率较高
def yundama_captcha(filename):
    username = 'hugol'
    password = 'lyg960926'
    appid = 6681
    appkey = 'b2b32282d67bd432e56b08774b999481'
    codetype = 1000
    timeout = 10
    yundama = YDMHttp(username, password, appid, appkey)
    text = yundama.decode(filename, codetype, timeout)
    return text


# 识别倒立文字所在图片中的坐标，并返回列表，可识别仅有一个或两个倒立文字的图片
def captcha_inverted_cn(filename):
    z = zheye()
    positions = z.Recognize(filename)
    result = []
    if len(positions) == 2:
        if positions[0][1] > positions[1][1]:
            result.append([positions[1][1], positions[1][0]])
            result.append([positions[0][1], positions[0][0]])
        else:
            result.append([positions[0][1], positions[0][0]])
            result.append([positions[1][1], positions[1][0]])
    else:
        result.append([positions[0][1], positions[0][0]])
    return result


# 获取用户代理，并存进数据库
def get_proxy():
    response = requests.get("http://111.231.77.152:9999/https.php?user=aqa314&pass=aqa314&count=249&tdsourcetag=s_pcqq_aiomsg")
    proxies = response.text.split("\n")
    for proxy in proxies:
        proxy = proxy.replace("\r", "").split(" ")
        ip_port = proxy[0]
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client['proxy_ip']
        id_collection = Collection(db, 'ip_pool')
        ip_dict = {}
        try:
            proxy_ls = ip_port.split(":")
            ip_dict["ip"] = proxy_ls[0]
            ip_dict["port"] = proxy_ls[1]
            ip_dict["user_id"] = proxy[1]
            ip_dict["user_password"] = proxy[2]
            id_collection.insert(ip_dict)
        except Exception as e:
            print(e.args)


# 从mongodb所存储的代理验证ip中随机获取ip，并返回ip,port,id,password
def get_random_ip():
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client['proxy_ip']
    id_collection = Collection(db, 'ip_pool')
    info = id_collection.aggregate([{"$sample": {"size": 1}}])
    for i in info:
        ip = i["ip"]
        port = i["port"]
        user_id = i["user_id"]
        user_password = i["user_password"]
        return ip, port, user_id, user_password
