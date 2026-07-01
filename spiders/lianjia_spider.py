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
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent

class LianjiaSpider:
    """链家重庆二手房爬虫"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://cq.lianjia.com/ershoufang/',
            'Connection': 'keep-alive'
        }
        self.storage = CSVStorage()
        self.total_count = 0
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
    
    def get_max_page(self, html):
        """获取最大页码"""
        soup = BeautifulSoup(html, 'lxml')
        page_box = soup.select_one('.page-box')
        if page_box:
            page_data = page_box.get('page-data')
            if page_data:
                try:
                    import json
                    data = json.loads(page_data)
                    return data.get('totalPage', 100)
                except:
                    pass
        
        page_nums = soup.select('.page-box a')
        if page_nums:
            try:
                return int(page_nums[-2].text)
            except:
                pass
        
        return 50
    
    def parse_list_page(self, html, district):
        """解析列表页"""
        soup = BeautifulSoup(html, 'lxml')
        items = soup.select('.sellListContent li')
        if not items:
            items = soup.select('.listContent li')
        if not items:
            items = soup.select('li[data-lj_action_housedel_id]')
        
        data_list = []
        
        for item in items:
            try:
                title_elem = item.select_one('.title a')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                house_info = item.select_one('.houseInfo')
                house_info_text = house_info.get_text(strip=True) if house_info else ''
                
                position_info = item.select_one('.positionInfo')
                position_info_text = position_info.get_text(strip=True) if position_info else ''
                
                total_price_elem = item.select_one('.totalPrice span')
                total_price = float(total_price_elem.get_text(strip=True)) if total_price_elem else 0
                
                unit_price_elem = item.select_one('.unitPrice')
                unit_price_text = unit_price_elem.get_text(strip=True) if unit_price_elem else ''
                unit_price_val = float(re.search(r'(\d+)', unit_price_text).group(1)) if re.search(r'(\d+)', unit_price_text) else 0
                
                area_match = re.search(r'(\d+(?:\.\d+)?)㎡', house_info_text)
                area = float(area_match.group(1)) if area_match else 0
                
                house_type_match = re.search(r'(\d+)室(\d+)厅', house_info_text)
                house_type = f"{house_type_match.group(1)}室{house_type_match.group(2)}厅" if house_type_match else ''
                
                tags = []
                tag_elements = item.select('.tag span')
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
        page = 1
        max_pages = 50
        has_data = True
        
        while page <= max_pages and has_data:
            try:
                page_url = f"{url}pg{page}/"
                logger.info(f"正在爬取 {district} 第{page}页: {page_url}")
                
                html = self.get(page_url)
                
                if not html:
                    logger.warning(f"{district} 第{page}页获取失败")
                    break
                
                if page == 1:
                    max_pages = min(max_pages, self.get_max_page(html))
                
                data_list = self.parse_list_page(html, district)
                
                if not data_list:
                    logger.info(f"{district} 第{page}页无数据，停止爬取")
                    has_data = False
                    break
                
                self.storage.insert_many(data_list)
                self.total_count += len(data_list)
                
                logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                
                page += 1
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"{district} 第{page}页爬取失败: {e}")
                break
    
    def crawl(self):
        """爬取入口"""
        logger.info("开始爬取链家重庆二手房数据")
        
        for district, url in self.district_urls.items():
            try:
                self.crawl_district(district, url)
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.error(f"爬取 {district} 失败: {e}")
        
        logger.info(f"链家爬取完成，总数据量: {self.total_count}条")

if __name__ == "__main__":
    spider = LianjiaSpider()
    spider.crawl()
