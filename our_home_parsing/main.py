from scrapy.crawler import CrawlerProcess
from our_home_parsing.spiders.our_home_spider import OurHomeSpider

def main():


    process = CrawlerProcess()

    process.crawl(OurHomeSpider)
    process.start() # the script will block here until the crawling is finished

if __name__ == '__main__':
    main()