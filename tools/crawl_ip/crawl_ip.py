import requests
from scrapy.selector import Selector
import pymysql
from fake_useragent import UserAgent

conn = pymysql.connect(host="localhost", user="root", password="root", db="ip_crawl", charset="utf8")
cursor = conn.cursor()
ua = UserAgent()
headers = {
    "User-Agent": ua.random
}


class IpCrawler(object):
    def crawl_ip(self):
        for i in range(1000):
            response = requests.get("https://www.xicidaili.com/nn/{0}".format(i), headers=headers)
            if response.status_code == 200:
                selector = Selector(text=response.text)
                ip_node = selector.xpath("//table[@id='ip_list']//tr")

                ip_list = []
                for ip in ip_node[1:]:
                    ip_address = ip.xpath("./td[2]/text()").extract()[0]
                    ip_port = ip.xpath("./td[3]/text()").extract()[0]
                    ip_type = ip.xpath("./td[5]/text()").extract()[0]
                    ip_scheme = ip.xpath("./td[6]/text()").extract()[0]
                    ip_speed = float((ip.xpath("./td[7]/div/@title").extract()[0]).split("秒")[0])

                    ip_list.append((ip_address, ip_port, ip_scheme, ip_speed, ip_type))

                for ip_info in ip_list:
                    cursor.execute(
                        "INSERT INTO ip_list(ip_address, ip_port, ip_scheme, ip_speed, ip_type)VALUES('{0}', '{1}', '{2}', {3}, '{4}')ON DUPLICATE KEY UPDATE ip_speed={5}".format(
                            ip_info[0], ip_info[1], ip_info[2], ip_info[3], ip_info[4], ip_info[3]
                        )
                    )
                    conn.commit()
            else:
                print(response.status_code)


class GetIP(object):
    def delete_ip(self, ip_address):
        delete_sql = """
            DELETE FROM ip_list WHERE ip_address='{0}'
            """.format(ip_address)
        cursor.execute(delete_sql)
        conn.commit()
        return True

    def judge_ip(self, ip_address, port, scheme):
        http_url = "http://www.baidu.com"
        if "HTTP" in scheme:
            proxy_url_http = "{0}://{1}:{2}".format(scheme, ip_address, port)
        elif "HTTPS" in scheme:
            proxy_url_https = "{0}://{1}:{2}".format(scheme, ip_address, port)
        else:
            print("has no suitable scheme")
        try:
            proxies = {
                "http": proxy_url_http,
                "https": proxy_url_https
            }
            response = requests.get(http_url, proxies=proxies)
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip_address)
            return False
        else:
            code = response.status_code
            if (code >= 200) and (code < 300):
                print("effective ip")
                return True
            else:
                print("invalid ip")
                self.delete_ip(ip_address)
                return False

    def get_random_ip(self):
        random_sql = """
                SELECT ip_address, ip_port, ip_scheme FROM ip_list
                ORDER BY RAND()
                LIMIT 1
                """
        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip_address = ip_info[0]
            port = ip_info[1]
            scheme = ip_info[2]

            judge_re = self.judge_ip(ip_address, port, scheme)
            if judge_re:
                return "{0}://{1}:{2}".format(scheme, ip_address, port)
            else:
                return self.get_random_ip()


# 爬取西刺ip
# ip_crawl = IpCrawler()
# ip_crawl.crawl_ip()

# 从数据库获取随机ip
get_ip = GetIP()
get_ip.get_random_ip()
