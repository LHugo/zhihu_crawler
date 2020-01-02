# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from twisted.enterprise import adbapi
import codecs
import json
from scrapy.exporters import JsonItemExporter
import pymysql
import pymysql.cursors
# import MySQLdb
# import MySQLdb.cursors


# 自定义json文件的导出
class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('file_name.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


# 调用scrapy提供的json_exporter导出成json文件
class JsonExporterPipeline(object):
    def __init__(self):
        self.file = open('filename.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


# 采用同步的机制将数据写入mysql数据库中
class MysqlPipeline(object):
    def __init__(self):
        self.connect = pymysql.connect('host', 'user', 'password', 'db_name', charset='utf8',
                                       use_unicode=True)
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):

        insert_sql = """
            insert into tb_name()
            values (%s{})"""
        self.cursor.execute(insert_sql, (item[''], item[''], item[''],
                                         item[''], item[''], item[''],
                                         item[''], item[''], item['']))
        self.connect.commit()


# 利用scrapy提供的twisted异步IO流将数据写入mysql数据库，防止数据在写入时发生堵塞
class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbpool = adbapi.ConnectionPool("pymysql", host=settings["MYSQL_HOST"], db=settings["MYSQL_DBNAME"],
                                       user=settings["MYSQL_USER"], passwd=settings["MYSQL_PASSWORD"], charset='utf8',
                                       cursorclass=pymysql.cursors.DictCursor, use_unicode=True)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        insert_sql, items = item.get_insert_sql()
        cursor.execute(insert_sql, items)

