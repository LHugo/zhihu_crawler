import re
import datetime
import hashlib
import tesserocr
from PIL import Image
from tools.yundama_requests.yundama_requests import YDMHttp
from tools.zheye import zheye


def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5(url)
    return m.hexdigest()


def extract_num(value):
    re_num = re.match(".*?(\d+).*", value)
    if re_num:
        num = int(re_num.group(1))
    else:
        num = 0
    return num


def date_convert(value):
    try:
        date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        print(e)
        date = datetime.datetime.now().date()
    return date


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


def yundama_captcha(filename):
    username = 'hugol'
    password = 'lyg960926'
    appid = 6681
    appkey = 'b2b32282d67bd432e56b08774b999481'
    codetype = 5000
    timeout = 30
    yundama = YDMHttp(username, password, appid, appkey)
    text = yundama.decode(filename, codetype, timeout)
    return text


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


captcha_inverted_cn(r"D:\PythonProjects\zhihu\utils\a.gif")
