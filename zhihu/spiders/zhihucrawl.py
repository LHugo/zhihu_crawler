# -*- coding: utf-8 -*-
import scrapy
import pickle
import time
from selenium import webdriver
from scrapy.loader import ItemLoader
from urllib import parse
from zhihu.items import ZhihuItemQuestion, ZhihuItemAnswer
import re
import json
import datetime
from utils.common import yundama_captcha
from scrapy.selector import Selector
import base64
from scrapy_redis.spiders import RedisSpider


class ZhihucrawlSpider(scrapy.Spider):
    name = 'zhihucrawl'
    allowed_domains = ['www.zhihu.com']
    KEY_WORD = "爬虫"
    start_url = ["https://www.zhihu.com/search?q={0}".format(KEY_WORD)]
    # redis_key = 'zhihucrawl:start_urls'
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit={1}&offset={2}&platform=desktop&sort_by=default"

    def start_requests(self):
        browser = webdriver.Chrome(executable_path="D:/Evns/py3scrapy/Scripts/chromedriver.exe")
        browser.get("https://www.zhihu.com/signin")
        browser.find_element_by_css_selector(".SignFlow-accountInput.Input-wrapper input").send_keys("13169188007")
        browser.find_element_by_css_selector(".SignFlow-password input").send_keys("lyg960926")
        browser.find_element_by_css_selector(".Button.SignFlow-submitButton").click()
        time.sleep(5)
        # # 知乎流量或IP异常验证
        # content = browser.page_source
        # if "异常流量" in content:
        #     selector = Selector(text=content)
        #     img_url = (selector.xpath("//div[@class='Unhuman-inputRow']/img/@src").extract()[0])
        #     img = (re.match('.*base64,(R.*)', img_url, re.S)).group(1)
        #     captcha_img = open("D:/PythonProjects/zhihu/tools/yundama_requests/captcha.png", "wb")
        #     captcha_img.write(base64.b64decode(img))
        #     captcha_img.close()
        #     time.sleep(10)
        #     captcha = yundama_captcha("D:/PythonProjects/zhihu/tools/yundama_requests/captcha.png")
        #     time.sleep(20)
        #     browser.find_element_by_xpath("//div[@class='Unhuman-inputRow']//input").send_keys(captcha)
        #     browser.find_element_by_xpath("//section[@class='Unhuman-verificationCode']//button").click()
        #     return [scrapy.Request(url=browser.current_url)]
        # else:
        cookies = browser.get_cookies()
        cookie_dict = {}
        for cookie in cookies:
            f = open('D:/PythonProjects/zhihu/cookies/zhihu/' + cookie['name'] + '.zhihu', 'wb+')
            pickle.dump(cookie, f)
            f.close()
            cookie_dict[cookie['name']] = cookie['value']
        browser.quit()
        return [scrapy.Request(url=self.start_url[0], dont_filter=True, cookies=cookie_dict)]

    def parse(self, response):
        browser = webdriver.Chrome(executable_path="D:/Evns/py3scrapy/Scripts/chromedriver.exe")
        browser.get(response.url)
        for i in range(1000):
            browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight); var lenOfPage=document.body.scrollHeight; return lenOfPage;")
        selector = Selector(text=browser.page_source)
        all_urls = selector.xpath("//div[@itemprop='zhihu:question']//a/@href").extract()
        all_urls = [parse.urljoin('https://www.zhihu.com', url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_url = re.match('(.*zhihu.com/question/(\d+))(/|$).*', url)
            if match_url:
                question_url = match_url.group(1)
                question_id = match_url.group(2)
                print(question_url, question_id)
                yield scrapy.Request(url=question_url, meta={"question_id": question_id}, callback=self.parse_question)
            # else:
            #     yield scrapy.Request(url=url, callback=self.parse)

    def parse_question(self, response):
        item_loader = ItemLoader(item=ZhihuItemQuestion(), response=response)
        item_loader.add_value("zhihu_id", response.meta.get("question_id"))
        item_loader.add_value("url", response.url)
        item_loader.add_xpath("title", "//h1[@class='QuestionHeader-title']//text()")
        item_loader.add_xpath("main_content", "//div[@class='QuestionHeader-detail']//text()")
        item_loader.add_xpath("tag", "//div[@class='QuestionHeader-topics']//text()")
        item_loader.add_xpath("focus_num", "//button[@class='Button NumberBoard-item Button--plain']//strong//text()")
        item_loader.add_xpath("click_num", "//div[@class='NumberBoard-item']//strong//text()")
        item_loader.add_xpath("comment_num", "normalize-space(//div[@class='QuestionHeader-Comment']/button/text()[1])")
        item_loader.add_xpath("answer_num", "normalize-space(//div[@class='List-header']//span//text()[1])")

        question_item = item_loader.load_item()

        yield scrapy.Request(url=self.start_answer_url.format(response.meta.get("question_id"), 20, 0),
                             callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        answer_json = json.loads(response.text)
        is_end = answer_json["paging"]["is_end"]
        next_url = answer_json["paging"]["next"]

        for answer in answer_json["data"]:
            answer_item = ZhihuItemAnswer()
            answer_item["answer_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author"] = answer["author"]["name"] if "name" in answer["author"] else None
            answer_item["main_content"] = answer["content"] if "content" in answer else answer["excerpt"]
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item
        if not is_end:
            yield scrapy.Request(url=next_url, callback=self.parse_answer)

    #
