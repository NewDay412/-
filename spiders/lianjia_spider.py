from .base_spider import BaseSpider
from config import Config
from loguru import logger
from storage.csv_storage import CSVStorage
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json

class LianjiaSpider(BaseSpider):
    """链家重庆二手房爬虫"""
    
    def __init__(self):
        super().__init__("链家爬虫")
        self.base_url = "https://cq.lianjia.com"
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
        self.api_url = "https://cq.lianjia.com/ershoufang/"
        self.storage = CSVStorage()
        self.total_count = 0
    
    def parse_list_page(self, html, district):
        """解析列表页"""
        soup = self.parse_html(html)
        items = soup.select('.sellListContent li')
        data_list = []
        
        for item in items:
            try:
                title = self.extract_text(item.select_one('.title a'))
                price_info = self.extract_text(item.select_one('.totalPrice'))
                unit_price = self.extract_text(item.select_one('.unitPrice'))
                house_info = self.extract_text(item.select_one('.houseInfo'))
                position_info = self.extract_text(item.select_one('.positionInfo'))
                follow_info = self.extract_text(item.select_one('.followInfo'))
                detail_url = self.extract_attr(item.select_one('.title a'), 'href')
                
                total_price = float(re.search(r'(\d+(?:\.\d+)?)', price_info).group(1)) if re.search(r'(\d+(?:\.\d+)?)', price_info) else 0
                unit_price_val = float(re.search(r'(\d+)', unit_price).group(1)) if re.search(r'(\d+)', unit_price) else 0
                
                area_match = re.search(r'(\d+)平米', house_info)
                area = float(area_match.group(1)) if area_match else 0
                
                if not title or total_price == 0:
                    continue
                
                data = {
                    'title': title,
                    'district': district,
                    'location': position_info,
                    'total_price': total_price,
                    'unit_price': unit_price_val,
                    'area': area,
                    'house_info': house_info,
                    'follow_info': follow_info,
                    'detail_url': detail_url,
                    'source': '链家',
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                data_list.append(data)
            except Exception as e:
                logger.warning(f"解析列表项失败: {e}")
        
        return data_list
    
    def crawl_district(self, district, url):
        """爬取单个区县的数据"""
        logger.info(f"开始爬取 {district}")
        page = 1
        max_pages = 100
        
        while page <= max_pages:
            try:
                page_url = f"{url}pg{page}/"
                response = self.get(page_url)
                data_list = self.parse_list_page(response.text, district)
                
                if not data_list:
                    logger.info(f"{district} 第{page}页无数据，停止爬取")
                    break
                
                with self.lock:
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                
                logger.info(f"{district} 第{page}页完成，累计: {self.total_count}条")
                page += 1
                
            except Exception as e:
                logger.error(f"{district} 第{page}页爬取失败: {e}")
                break
    
    def crawl(self):
        """爬取入口"""
        logger.info("开始爬取链家重庆二手房数据")
        
        with ThreadPoolExecutor(max_workers=Config.SPIDER_SETTINGS["MAX_WORKERS"]) as executor:
            futures = []
            
            for district, url in self.district_urls.items():
                future = executor.submit(self.crawl_district, district, url)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"线程执行失败: {e}")
        
        logger.info(f"链家爬取完成，总数据量: {self.total_count}条")
        self.storage.close()
        self.close()

if __name__ == "__main__":
    spider = LianjiaSpider()
    spider.crawl()
