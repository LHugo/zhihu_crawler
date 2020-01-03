# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import datetime
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from scrapy.loader import ItemLoader
from utils.common import extract_num


class DefaultItemLoader(ItemLoader):
    default_output_processor = TakeFirst()


def return_value(value):
    return value


def date_convert(value):
    try:
        date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    return date


class ZhihuItemQuestion(scrapy.Item):
    tag = scrapy.Field()
    title = scrapy.Field()
    main_content = scrapy.Field()
    focus_num = scrapy.Field()
    click_num = scrapy.Field()
    comment_num = scrapy.Field()
    answer_num = scrapy.Field()
    url = scrapy.Field()
    zhihu_id = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO zhihu_question(zhihu_id, tag, url, title, main_content, click_num, focus_num,
                        comment_num, answer_num, crawl_time)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE answer_num=VALUES(answer_num),comment_num=VALUES(comment_num),
                                    click_num=VALUES(click_num),focus_num=VALUES(focus_num)           
        """
        zhihu_id = int("".join(self["zhihu_id"]))
        tag = "/".join(self["tag"])
        title = "".join(self["title"])
        main_content = "".join(self["main_content"]).replace("显示全部", "")
        focus_num = extract_num("".join(self["focus_num"]))
        click_num = extract_num("".join(self["click_num"]))
        comment_num = extract_num("".join(self["comment_num"]))
        answer_num = extract_num("".join(self["answer_num"]))
        url = self["url"][0]
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        items = (zhihu_id, tag, url, title, main_content, click_num, comment_num, answer_num, focus_num, crawl_time)

        return insert_sql, items


class ZhihuItemAnswer(scrapy.Item):
    url = scrapy.Field()
    question_id = scrapy.Field()
    answer_id = scrapy.Field()
    author = scrapy.Field()
    main_content = scrapy.Field()
    brief_content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            INSERT INTO zhihu_answer(question_id, answer_id, url, author, main_content, praise_num, comments_num,
                        create_time, update_time, crawl_time)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s )
            ON DUPLICATE KEY UPDATE main_content=VALUES(main_content),comments_num=VALUES(comments_num),
                                    praise_num=VALUES(praise_num), update_time=VALUES(update_time)
        """
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime("%Y-%m-%d")
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime("%Y-%m-%d")
        items = (self["question_id"], self["answer_id"], self["url"], self["author"], self["brief_content"],
                 self["praise_num"], self["comments_num"], create_time, update_time,
                 self["crawl_time"].strftime("%Y-%m-%d %H:%M:%S"))

        return insert_sql, items
