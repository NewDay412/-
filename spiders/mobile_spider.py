import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import re
import time
import random
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from fake_useragent import UserAgent

class MobileSpider:
    """移动端爬虫（安居客+链家）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        }
        self.storage = CSVStorage()
        self.total_count = 0
        self.districts = Config.CHONGQING_DISTRICTS
    
    def get(self, url):
        """发送请求"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                logger.debug(f"请求成功: {url}")
                return response.text
            else:
                logger.warning(f"请求失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return None
    
    def parse_anjuke_mobile(self, html, district):
        """解析安居客移动端"""
        soup = BeautifulSoup(html, 'lxml')
        items = soup.select('.list-item')
        
        data_list = []
        
        for item in items:
            try:
                title_elem = item.select_one('.title')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                price_elem = item.select_one('.price')
                price_text = price_elem.get_text(strip=True) if price_elem else ''
                
                unit_price_elem = item.select_one('.unit-price')
                unit_price_text = unit_price_elem.get_text(strip=True) if unit_price_elem else ''
                
                area_elem = item.select_one('.area')
                area_text = area_elem.get_text(strip=True) if area_elem else ''
                
                position_elem = item.select_one('.position')
                position_text = position_elem.get_text(strip=True) if position_elem else ''
                
                total_price = float(re.search(r'(\d+(?:\.\d+)?)', price_text).group(1)) if re.search(r'(\d+(?:\.\d+)?)', price_text) else 0
                unit_price_val = float(re.search(r'(\d+)', unit_price_text).group(1)) if re.search(r'(\d+)', unit_price_text) else 0
                
                area_match = re.search(r'(\d+(?:\.\d+)?)㎡', area_text)
                area = float(area_match.group(1)) if area_match else 0
                
                if unit_price_val == 0 and total_price > 0 and area > 0:
                    unit_price_val = round(total_price * 10000 / area, 0)
                
                if not title or total_price == 0:
                    continue
                
                data = {
                    'title': title,
                    'district': district,
                    'location': position_text,
                    'total_price': total_price,
                    'unit_price': unit_price_val,
                    'area': area,
                    'house_type': '',
                    'tags': '',
                    'detail_url': '',
                    'source': '安居客移动端',
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'insert_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'update_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                data_list.append(data)
            except Exception as e:
                logger.warning(f"解析安居客移动端列表项失败: {e}")
        
        return data_list
    
    def crawl_anjuke_mobile(self):
        """爬取安居客移动端"""
        logger.info("开始爬取安居客移动端数据")
        
        for district in self.districts:
            try:
                district_pinyin = {
                    "渝中区": "yuzhongqu",
                    "大渡口区": "dadukou",
                    "江北区": "jiangbei",
                    "沙坪坝区": "shapingba",
                    "九龙坡区": "jiulongpo",
                    "南岸区": "nanan",
                    "北碚区": "beibei",
                    "渝北区": "yubeiqu",
                    "巴南区": "banan",
                    "万州区": "wanzhou",
                    "涪陵区": "fuling",
                    "长寿区": "changshou",
                    "江津区": "jiangjin",
                    "合川区": "hechuan",
                    "永川区": "yongchuan",
                    "南川区": "nanchuan",
                    "綦江区": "qijiang",
                    "大足区": "dazu",
                    "璧山区": "bishan",
                    "铜梁区": "tongliang",
                    "潼南区": "tongnan",
                    "荣昌区": "rongchang",
                    "开州区": "kaizhou",
                    "梁平区": "liangping",
                    "武隆区": "wulong"
                }.get(district, district)
                
                page = 1
                max_pages = 100
                has_data = True
                
                while page <= max_pages and has_data:
                    url = f"https://m.anjuke.com/cq/sale/{district_pinyin}/p{page}/"
                    logger.info(f"正在爬取安居客移动端 {district} 第{page}页: {url}")
                    
                    html = self.get(url)
                    
                    if not html:
                        logger.warning(f"{district} 第{page}页获取失败")
                        break
                    
                    data_list = self.parse_anjuke_mobile(html, district)
                    
                    if not data_list:
                        logger.info(f"{district} 第{page}页无数据，停止爬取")
                        has_data = False
                        break
                    
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    
                    logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                    
                    page += 1
                    time.sleep(random.uniform(1, 2))
                
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                logger.error(f"爬取安居客移动端 {district} 失败: {e}")
        
        logger.info(f"安居客移动端爬取完成，总数据量: {self.total_count}条")
    
    def crawl(self):
        """爬取入口"""
        self.crawl_anjuke_mobile()

if __name__ == "__main__":
    spider = MobileSpider()
    spider.crawl()
