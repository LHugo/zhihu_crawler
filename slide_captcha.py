from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as Ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import os
import random
import cv2
import numpy as np
import undetected_chromedriver.v2 as uc
import pickle


class Code():
    def __init__(self, slider_ele=None, background_ele=None, count=1, save_image=False):
        self.count = count
        self.save_images = save_image
        self.slider_ele = slider_ele
        self.background_ele = background_ele

    def get_slide_locus(self, distance):
        # 由于计算机计算的误差，导致模拟人类行为时，会出现分布移动总和大于真实距离，这里就把这个差值加到distance上去
        distance += 8
        v = 0
        t = 0.5
        # 保存每0.5内的滑动的距离
        tracks = []
        current = 0
        mid = distance * 4 / 5
        while current <= distance:
            # 滑块初始加速度为正，过mid点后加速度变为负数
            if current < mid:
                a = 2
            else:
                a = -3

            s = v * t + 0.5 * a * (t ** 2)
            current += s
            tracks.append(round(s))
            v = v + a * t

        return tracks

    def slide_verification(self, driver, slide_element, distance):
        # 根据滑动的距离生成滑动轨迹
        locus = self.get_slide_locus(distance)

        # 按下鼠标左键
        ActionChains(driver).click_and_hold(slide_element).perform()

        time.sleep(0.5)

        # 遍历轨迹进行滑动
        for loc in locus:
            time.sleep(0.01)
            ActionChains(driver).move_by_offset(loc, random.randint(-5, 5)).perform()
            ActionChains(driver).context_click(slide_element)

        # 释放鼠标
        ActionChains(driver).release(on_element=slide_element).perform()

    def onload_save_img(self, url, filename="image.png"):
        try:
            response = requests.get(url)
        except Exception as e:
            print('图片下载失败')
            raise e
        else:
            with open(filename, 'wb') as f:
                f.write(response.content)

    def get_element_slide_distance(self, slider_img, background_img, correct=0):
        # 获取验证码的图片
        slider_url = slider_img.get_attribute('src')
        background_url = background_img.get_attribute('src')

        # 下载并保存滑块和背景图片
        slider = 'slider.jpg'
        background = 'background.jpg'

        self.onload_save_img(slider_url, slider)

        self.onload_save_img(background_url, background)

        # 进行色度图片, 转化为numpy中的数组类型数据
        slider_pic = cv2.imread(slider, 0)
        background_pic = cv2.imread(background, 0)

        # 获取缺口数组的形状
        width, height = slider_pic.shape[::-1]

        # 将处理之后的图片另存
        slider01 = 'slider01.jpg'
        slider02 = 'slider02.jpg'
        background01 = 'background01.jpg'

        cv2.imwrite(slider01, slider_pic)
        cv2.imwrite(background01, background_pic)

        # 读取另存的滑块
        slider_pic = cv2.imread(slider01)

        # 进行色彩转化
        slider_pic = cv2.cvtColor(slider_pic, cv2.COLOR_BGR2GRAY)

        # 获取色差的绝对值
        slider_pic = abs(255 - slider_pic)
        # 保存图片
        cv2.imwrite(slider02, slider_pic)
        # 读取滑块
        slider_pic = cv2.imread(slider02)

        # 读取背景图
        background_pic = cv2.imread(background01)
        time.sleep(3)

        # 寻找两张图的重叠部分
        result = cv2.matchTemplate(slider_pic, background_pic, cv2.TM_CCOEFF_NORMED)

        # 通过数组运算，获取图片缺口位置
        top, left = np.unravel_index(result.argmax(), result.shape)

        # 判断是否需要保存识别过程中的截图文件
        if self.save_images:
            loc = [(left + correct, top + correct), (left + width - correct, top + height - correct)]
            self.image_crop(background, loc)

        else:
            # 删除临时文件
            os.remove(slider01)
            os.remove(slider02)
            os.remove(background01)
            os.remove(background)
            os.remove(slider)
        # 返回需要移动的位置距离
        return left

    def image_crop(self, image, loc):
        cv2.rectangle(image, loc[0], loc[1], (7, 249, 151), 2)
        cv2.imshow('Show', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


class Login(object):
    def __init__(self, user, password, keyword, retry):
        # 创建一个参数对象，用来控制chrome以无界面模式打开
        chrome_options = webdriver.ChromeOptions()
        # 禁用GPU加速
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')

        self.browser = uc.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.url = 'https://www.zhihu.com/signin'
        self.sli = Code()
        self.user = user
        self.password = password
        self.keyword = keyword
        self.cookies = {}
        # 失败重试次数
        self.retry = retry

    def login(self):
        self.browser.get(self.url)
        login_element = self.browser.find_element(By.XPATH,
            '//*[@id="root"]/div/main/div/div/div/div[1]/div/div[1]/form/div[1]/div[2]')
        self.browser.execute_script("arguments[0].click();", login_element)
        time.sleep(2)
        # 输入账号
        username = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-account input'))
        )
        username.send_keys(self.user)
        # 输入密码
        password = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.SignFlow-password input'))
        )
        password.send_keys(self.password)
        # 点击登录
        submit = self.wait.until(
            Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
        )
        time.sleep(1)
        submit.click()
        time.sleep(2)

        k = 1
        while k < self.retry:
            # 获取原图url
            bg_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_bg-img'))
            )
            # 获取滑块url
            front_img = self.wait.until(
                Ec.presence_of_element_located((By.CSS_SELECTOR, '.yidun_bgimg .yidun_jigsaw'))
            )
            # 获取验证码实际需要滑动的距离
            distance = self.sli.get_element_slide_distance(front_img, bg_img)
            distance = distance - 4

            # 滑块对象
            element = self.browser.find_element(By.CSS_SELECTOR,
                '.yidun_slider')
            # 拖曳滑动
            self.sli.slide_verification(self.browser, element, distance)

            # 滑动之后的url链接
            time.sleep(5)
            # 登录框
            try:
                submit = self.wait.until(
                    Ec.element_to_be_clickable((By.CSS_SELECTOR, '.Button.SignFlow-submitButton'))
                )
                submit.click()
                time.sleep(3)
            except:
                pass

            end_url = self.browser.current_url

            if end_url == "https://www.zhihu.com/":
                try:
                    search_con = self.wait.until(
                        Ec.element_to_be_clickable((By.CSS_SELECTOR, '#Popover1-toggle'))
                    )
                    search_con.send_keys(self.keyword)
                    search = self.wait.until(
                        Ec.element_to_be_clickable((By.CSS_SELECTOR, '#root > div > div:nth-child(2) > header > div.AppHeader-inner.css-qqgmyv > div.css-1acwmmj > div > form > div > div > label > button'))
                    )
                    search.click()
                    time.sleep(1)
                except:
                    pass
                return self.get_cookies()
            else:
                time.sleep(3)
                k += 1

        return None

    def get_cookies(self):
        cookies_dic = self.browser.get_cookies()
        for cookie in cookies_dic:
        #     with open('D:/PythonProjects/zhihu/cookies/zhihu.cookie', 'wb')as f:
        #         pickle.dump(cookie, f)
            self.cookies[cookie['name']] = cookie['value']
        # self.cookies = ''
        # for cookie in cookies_dic:
        #     self.cookies += '{}={};'.format(cookie.get('name'), cookie.get('value'))
        print(self.cookies)
        self.browser.close()

        return self.cookies

    # def __del__(self):
    #     self.browser.close()
    #     print('界面关闭')

#
# if __name__ == "__main__":
#     l = Login("13169188007", "lyg960926", 'python', 5)
#     cookies_dict = l.login()
