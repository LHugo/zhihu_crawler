from scrapy.cmdline import execute
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# os.system('chrome --remote-debugging-port=9222')
execute(['scrapy', 'crawl', 'zhihucrawl'])

