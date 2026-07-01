import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
import time
import random
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class BrowserSpider:
    """浏览器自动化爬虫（绕过反爬）"""
    
    def __init__(self):
        self.storage = CSVStorage()
        self.total_count = 0
        self.driver = None
        self.base_url = "https://chongqing.anjuke.com"
        self.district_urls = {
            "渝中区": "https://chongqing.anjuke.com/sale/yuzhongqu/",
            "大渡口区": "https://chongqing.anjuke.com/sale/dadukou/",
            "江北区": "https://chongqing.anjuke.com/sale/jiangbei/",
            "沙坪坝区": "https://chongqing.anjuke.com/sale/shapingba/",
            "九龙坡区": "https://chongqing.anjuke.com/sale/jiulongpo/",
            "南岸区": "https://chongqing.anjuke.com/sale/nanan/",
            "北碚区": "https://chongqing.anjuke.com/sale/beibei/",
            "渝北区": "https://chongqing.anjuke.com/sale/yubeiqu/",
            "巴南区": "https://chongqing.anjuke.com/sale/banan/",
            "万州区": "https://chongqing.anjuke.com/sale/wanzhou/",
            "涪陵区": "https://chongqing.anjuke.com/sale/fuling/",
            "长寿区": "https://chongqing.anjuke.com/sale/changshou/",
            "江津区": "https://chongqing.anjuke.com/sale/jiangjin/",
            "合川区": "https://chongqing.anjuke.com/sale/hechuan/",
            "永川区": "https://chongqing.anjuke.com/sale/yongchuan/",
            "南川区": "https://chongqing.anjuke.com/sale/nanchuan/",
            "綦江区": "https://chongqing.anjuke.com/sale/qijiang/",
            "大足区": "https://chongqing.anjuke.com/sale/dazu/",
            "璧山区": "https://chongqing.anjuke.com/sale/bishan/",
            "铜梁区": "https://chongqing.anjuke.com/sale/tongliang/",
            "潼南区": "https://chongqing.anjuke.com/sale/tongnan/",
            "荣昌区": "https://chongqing.anjuke.com/sale/rongchang/",
            "开州区": "https://chongqing.anjuke.com/sale/kaizhou/",
            "梁平区": "https://chongqing.anjuke.com/sale/liangping/",
            "武隆区": "https://chongqing.anjuke.com/sale/wulong/",
        }
    
    def init_driver(self):
        """初始化浏览器驱动"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--accept-language=zh-CN,zh;q=0.9')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        logger.info("浏览器驱动初始化成功")
    
    def close_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器驱动已关闭")
    
    def get_page(self, url):
        """获取页面"""
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 4))
            return self.driver.page_source
        except TimeoutException:
            logger.warning(f"页面加载超时: {url}")
            return None
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return None
    
    def parse_list_page(self, html, district):
        """解析列表页"""
        soup = BeautifulSoup(html, 'lxml')
        items = soup.select('.property-ex')
        data_list = []
        
        for item in items:
            try:
                title = item.select_one('.property-content-title-name')
                title = title.get_text(strip=True) if title else ''
                
                price_total = item.select_one('.property-price-total')
                price_total = price_total.get_text(strip=True) if price_total else ''
                
                price_avg = item.select_one('.property-price-average')
                price_avg = price_avg.get_text(strip=True) if price_avg else ''
                
                info = item.select_one('.property-content-info')
                info = info.get_text(strip=True) if info else ''
                
                address = item.select_one('.property-content-address')
                address = address.get_text(strip=True) if address else ''
                
                tags = []
                tag_elements = item.select('.property-content-tag span')
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)
                
                detail_url = item.select_one('.property-content-title-name')
                detail_url = detail_url['href'] if detail_url and 'href' in detail_url.attrs else ''
                
                total_price = float(re.search(r'(\d+(?:\.\d+)?)', price_total).group(1)) if re.search(r'(\d+(?:\.\d+)?)', price_total) else 0
                unit_price_val = float(re.search(r'(\d+)', price_avg).group(1)) if re.search(r'(\d+)', price_avg) else 0
                
                area_match = re.search(r'(\d+(?:\.\d+)?)㎡', info)
                area = float(area_match.group(1)) if area_match else 0
                
                if not title or total_price == 0:
                    continue
                
                data = {
                    'title': title,
                    'district': district,
                    'location': address,
                    'total_price': total_price,
                    'unit_price': unit_price_val,
                    'area': area,
                    'tags': ','.join(tags),
                    'detail_url': detail_url,
                    'source': '安居客',
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'insert_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'update_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                data_list.append(data)
            except Exception as e:
                logger.warning(f"解析列表项失败: {e}")
        
        return data_list
    
    def crawl_district(self, district, url):
        """爬取单个区县"""
        logger.info(f"开始爬取 {district}")
        self.init_driver()
        
        page = 1
        max_pages = 50
        has_data = True
        
        while page <= max_pages and has_data:
            try:
                page_url = f"{url}p{page}/"
                logger.info(f"正在爬取 {district} 第{page}页: {page_url}")
                
                html = self.get_page(page_url)
                
                if not html:
                    logger.warning(f"{district} 第{page}页获取失败")
                    break
                
                data_list = self.parse_list_page(html, district)
                
                if not data_list:
                    logger.info(f"{district} 第{page}页无数据，停止爬取")
                    has_data = False
                    break
                
                self.storage.insert_many(data_list)
                self.total_count += len(data_list)
                
                logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                
                page += 1
                
                if page % 5 == 0:
                    time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                logger.error(f"{district} 第{page}页爬取失败: {e}")
                break
        
        self.close_driver()
    
    def crawl(self):
        """爬取入口"""
        logger.info("开始使用浏览器爬虫爬取安居客数据")
        
        for district, url in self.district_urls.items():
            try:
                self.crawl_district(district, url)
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                logger.error(f"爬取 {district} 失败: {e}")
        
        logger.info(f"浏览器爬虫完成，总数据量: {self.total_count}条")

if __name__ == "__main__":
    spider = BrowserSpider()
    spider.crawl()
