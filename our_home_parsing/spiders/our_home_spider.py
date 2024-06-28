import time
import scrapy
from scrapy import Selector

from fake_useragent import UserAgent

from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from scrapy_selenium import SeleniumRequest


class OurHomeSpider(scrapy.Spider):
    options: Options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={UserAgent().random}")
    service: Service = Service(ChromeDriverManager().install())
    driver: webdriver = webdriver.ChromiumDriver(service=service, options=options)

    name = "our_home_spider"
    allowed_domains = ["наш.дом.рф", 'xn--80az8a.xn--d1aqf.xn--p1ai']

    def start_requests(self):
        url: str = 'https://xn--80az8a.xn--d1aqf.xn--p1ai/%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B/%D0%BA%D0%B0%D1%82%D0%B0%D0%BB%D0%BE%D0%B3-%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D1%80%D0%BE%D0%B5%D0%BA/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA-%D0%BE%D0%B1%D1%8A%D0%B5%D0%BA%D1%82%D0%BE%D0%B2/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA?place=0-44&objStatus=0'

        content = self.scroll_and_click(url)
        
        selector = Selector(text=content)
        ads_items = selector.css('.NewBuildingItem__Wrapper-sc-o36w9y-0.iYDe')

        for item in ads_items[:5]:
            href = item.css('.NewBuildingItem__MainTitle-sc-o36w9y-6.KYYzh::attr(href)').get()
            if 'https://xn--80az8a.xn--d1aqf.xn--p1ai/' not in href:
                href = 'https://xn--80az8a.xn--d1aqf.xn--p1ai/' + href
            yield SeleniumRequest(url=href, callback=self.parse, wait_time=2)

    def parse(self, response, **kwargs):
        self.driver.get(response.url)

        content = self.driver.page_source

        selector = Selector(text=content)

        title_text = selector.css('title::text').get()
        header_text = selector.css('h1.Header__Name-sc-eng632-3.fSjDTR::text').get()
        address_text = selector.css('p.Header__Address-sc-eng632-8.ciJBjz::text').getall()
        for elem in title_text.split('|'):
            if "ID" in elem:
                object_id = elem.strip()
                break

        result = {
            'Link': response.url,
            'Заголовок': header_text,
            'Адрес': ''.join(address_text).strip(),
            'ID объявления': object_id.replace('ID дома: ', ''),
        }

        attributes = {'Ввод в эксплуатацию', 'Застройщик', 'Группа компаний', 'Дата публикации проекта', 'Выдача ключей', 'Средняя цена за 1 м²', 'Распроданность квартир', 'Класс недвижимости', 'Количество недвижимости'}

        # парсим данные с верхнего блока
        developer_container = selector.css('div.Developer__Container-sc-kydjcf-1.hMdDdq')
        for row_div in developer_container.css('div.Row-sc-13pfgqd-0.dJkQFS'):
            label = row_div.css('div.Row__Name-sc-13pfgqd-1.fibhMt::text').get().strip()
            date_publication_or_none = row_div.css('div.Developer__Decl-sc-kydjcf-0.kBSRPf::text').getall()
            link_or_none = row_div.css('a.Link__LinkContainer-sc-1u7ca6h-0.hYekpU::text').getall()
            comon_text_or_none = row_div.css('div.Row__Value-sc-13pfgqd-2.dySlPJ::text').getall()
            if date_publication_or_none:
                extra_data = "".join(date_publication_or_none).strip()
            elif  link_or_none:
                extra_data = "".join(link_or_none).strip()
            elif comon_text_or_none:
                extra_data = "".join(comon_text_or_none).strip()

            if label in attributes:
                result[label] = extra_data
                attributes.remove(label)

        houseinfo_container = selector.css('div.HouseInfo__Container-sc-17wkiw0-0.ehPoPM')
        for row_div in houseinfo_container.css('div.Row-sc-13pfgqd-0.dJkQFS'):
            label = row_div.css('div.Row__Name-sc-13pfgqd-1.fibhMt::text').getall()
            attribute = ''.join(label).strip()
            row_value = row_div.css('div.Row__Value-sc-13pfgqd-2.dySlPJ::text').getall()
            value = ''.join(row_value).strip()
            if attribute in attributes:
                result[attribute] = value
                attributes.remove(attribute)
        # парсим данные из основных хорактеристик 
        additional_info = selector.css('div.AdditionalInfo__Wrapper-sc-2i4wxn-0.guywAG')
        for elem in additional_info.css('div.CharacteristicsBlock__CharacteristicsWrapper-sc-1fyyfia-0.hLSInZ'):
            for character in elem.css('div.CharacteristicsBlock__Row-sc-1fyyfia-3.cIsqar'):
                temp = character.css('span.CharacteristicsBlock__RowSpan-sc-1fyyfia-4.eCBXEE::text').getall()
                if temp[0] in attributes:
                    result[temp[0]] = temp[1]
                    attributes.remove(temp[0])

        for attribute in attributes:
            result[attribute] = '-'

        yield result 


    def scroll_and_click(self, url):
        self.driver.get(url)

        time.sleep(3)

        try:
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                self.driver.find_element(By.CSS_SELECTOR, 'button.styles__ButtonWrapper-sc-40tof2-0.kYqzc.Newbuildings__ButtonLoadMore-sc-1bou0u4-15.bpTAvq').click()
                time.sleep(3)
        except:
            return self.driver.page_source

