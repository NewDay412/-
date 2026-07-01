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

class LianjiaBrowserSpider:
    """链家浏览器爬虫"""
    
    def __init__(self):
        self.storage = CSVStorage()
        self.total_count = 0
        self.driver = None
        self.district_urls = {
            "渝中区": "https://cq.lianjia.com/ershoufang/yuzhong/",
            "大渡口区": "https://cq.lianjia.com/ershoufang/dadukou/",
            "江北区": "https://cq.lianjia.com/ershoufang/jiangbei/",
            "沙坪坝区": "https://cq.lianjia.com/ershoufang/shapingba/",
            "九龙坡区": "https://cq.lianjia.com/ershoufang/jiulongpo/",
            "南岸区": "https://cq.lianjia.com/ershoufang/nan/an/",
            "北碚区": "https://cq.lianjia.com/ershoufang/beibei/",
            "渝北区": "https://cq.lianjia.com/ershoufang/yubei/",
            "巴南区": "https://cq.lianjia.com/ershoufang/banan/",
            "万州区": "https://cq.lianjia.com/ershoufang/wanzhou/",
            "涪陵区": "https://cq.lianjia.com/ershoufang/fuling/",
            "长寿区": "https://cq.lianjia.com/ershoufang/changshou/",
            "江津区": "https://cq.lianjia.com/ershoufang/jiangjin/",
            "合川区": "https://cq.lianjia.com/ershoufang/hechuan/",
            "永川区": "https://cq.lianjia.com/ershoufang/yongchuan/",
            "南川区": "https://cq.lianjia.com/ershoufang/nanchuan/",
            "綦江区": "https://cq.lianjia.com/ershoufang/qijiang/",
            "大足区": "https://cq.lianjia.com/ershoufang/dazu/",
            "璧山区": "https://cq.lianjia.com/ershoufang/bishan/",
            "铜梁区": "https://cq.lianjia.com/ershoufang/tongliang/",
            "潼南区": "https://cq.lianjia.com/ershoufang/tongnan/",
            "荣昌区": "https://cq.lianjia.com/ershoufang/rongchang/",
            "开州区": "https://cq.lianjia.com/ershoufang/kaizhou/",
            "梁平区": "https://cq.lianjia.com/ershoufang/liangping/",
            "武隆区": "https://cq.lianjia.com/ershoufang/wulong/",
        }
    
    def init_driver(self):
        """初始化浏览器"""
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
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器驱动已关闭")
    
    def get_page(self, url):
        """获取页面"""
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 5))
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
        
        items = soup.select('.sellListContent li')
        if not items:
            items = soup.select('.listContent li')
        if not items:
            items = soup.select('li[data-lj_action_housedel_id]')
        if not items:
            items = soup.select('.house-lst li')
        if not items:
            items = soup.select('ul li div[class*="info"]')
        
        data_list = []
        
        for item in items:
            try:
                title_elem = item.select_one('.title a') or item.select_one('h2 a') or item.select_one('.property-content-title-name')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                house_info = item.select_one('.houseInfo') or item.select_one('.property-content-info')
                house_info_text = house_info.get_text(strip=True) if house_info else ''
                
                position_info = item.select_one('.positionInfo') or item.select_one('.property-content-address')
                position_info_text = position_info.get_text(strip=True) if position_info else ''
                
                total_price_elem = item.select_one('.totalPrice span') or item.select_one('.property-price-total')
                total_price = float(total_price_elem.get_text(strip=True)) if total_price_elem else 0
                
                unit_price_elem = item.select_one('.unitPrice') or item.select_one('.property-price-average')
                unit_price_text = unit_price_elem.get_text(strip=True) if unit_price_elem else ''
                unit_price_val = float(re.search(r'(\d+)', unit_price_text).group(1)) if re.search(r'(\d+)', unit_price_text) else 0
                
                area_match = re.search(r'(\d+(?:\.\d+)?)㎡', house_info_text)
                area = float(area_match.group(1)) if area_match else 0
                
                house_type_match = re.search(r'(\d+)室(\d+)厅', house_info_text)
                house_type = f"{house_type_match.group(1)}室{house_type_match.group(2)}厅" if house_type_match else ''
                
                tags = []
                tag_elements = item.select('.tag span') or item.select('.property-content-tag span')
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)
                
                detail_url = title_elem['href'] if title_elem and 'href' in title_elem.attrs else ''
                
                if not title or total_price == 0:
                    continue
                
                data = {
                    'title': title,
                    'district': district,
                    'location': position_info_text,
                    'total_price': total_price,
                    'unit_price': unit_price_val,
                    'area': area,
                    'house_type': house_type,
                    'tags': ','.join(tags),
                    'detail_url': detail_url,
                    'source': '链家',
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
                page_url = f"{url}pg{page}/"
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
        logger.info("开始使用浏览器爬虫爬取链家数据")
        
        for district, url in self.district_urls.items():
            try:
                self.crawl_district(district, url)
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                logger.error(f"爬取 {district} 失败: {e}")
        
        logger.info(f"链家浏览器爬虫完成，总数据量: {self.total_count}条")

if __name__ == "__main__":
    spider = LianjiaBrowserSpider()
    spider.crawl()
