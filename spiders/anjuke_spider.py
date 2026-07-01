from .base_spider import BaseSpider
from config import Config
from loguru import logger
from storage.csv_storage import CSVStorage
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class AnjukeSpider(BaseSpider):
    """安居客重庆二手房爬虫"""
    
    def __init__(self):
        super().__init__("安居客爬虫")
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
        self.storage = CSVStorage()
        self.total_count = 0
    
    def parse_list_page(self, html, district):
        """解析列表页"""
        soup = self.parse_html(html)
        items = soup.select('.property-ex')
        data_list = []
        
        for item in items:
            try:
                title = self.extract_text(item.select_one('.property-content-title-name'))
                price_info = self.extract_text(item.select_one('.property-price-total'))
                unit_price = self.extract_text(item.select_one('.property-price-average'))
                area_info = self.extract_text(item.select_one('.property-content-info'))
                location = self.extract_text(item.select_one('.property-content-address'))
                tags = [self.extract_text(tag) for tag in item.select('.property-content-tag span')]
                detail_url = self.extract_attr(item.select_one('.property-content-title-name'), 'href')
                
                if not detail_url:
                    detail_url = self.extract_attr(item.select_one('.property-content-title'), 'href')
                
                total_price = float(re.search(r'(\d+(?:\.\d+)?)', price_info).group(1)) if re.search(r'(\d+(?:\.\d+)?)', price_info) else 0
                unit_price_val = float(re.search(r'(\d+)', unit_price).group(1)) if re.search(r'(\d+)', unit_price) else 0
                
                area_match = re.search(r'(\d+(?:\.\d+)?)㎡', area_info)
                area = float(area_match.group(1)) if area_match else 0
                
                if not title or total_price == 0:
                    continue
                
                data = {
                    'title': title,
                    'district': district,
                    'location': location,
                    'total_price': total_price,
                    'unit_price': unit_price_val,
                    'area': area,
                    'tags': tags,
                    'detail_url': detail_url,
                    'source': '安居客',
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
        max_pages = 50
        
        while page <= max_pages:
            try:
                page_url = f"{url}p{page}/"
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
        logger.info("开始爬取安居客重庆二手房数据")
        
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
        
        logger.info(f"安居客爬取完成，总数据量: {self.total_count}条")
        self.storage.close()
        self.close()

if __name__ == "__main__":
    spider = AnjukeSpider()
    spider.crawl()
