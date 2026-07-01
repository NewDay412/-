import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import re
import time
import random
import math
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from fake_useragent import UserAgent

class CombinedSpider:
    """综合爬虫（安居客+链家，requests+Cookie方式）"""
    
    def __init__(self, cookies=None):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.storage = CSVStorage()
        self.total_count = 0
        self.cookies = cookies or {}
        
        self.districts = Config.CHONGQING_DISTRICTS
        
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        })
        
        if self.cookies:
            self.session.cookies.update(self.cookies)
    
    def random_delay(self, min_sec=0.5, max_sec=1.5):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def get(self, url, params=None, headers=None):
        """发送请求"""
        try:
            self.random_delay(0.8, 1.5)
            
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                logger.debug(f"请求成功: {url}")
                return response.text
            
            elif response.status_code == 401 or response.status_code == 302:
                logger.warning(f"需要登录或被重定向，状态码: {response.status_code}")
                return None
            
            else:
                logger.warning(f"请求失败，状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
    
    def parse_anjuke_list(self, html, district):
        """解析安居客列表页"""
        soup = BeautifulSoup(html, 'lxml')
        items = soup.select('.property-ex')
        
        data_list = []
        
        for item in items:
            try:
                title_elem = item.select_one('.property-content-title-name')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                price_total = item.select_one('.property-price-total')
                price_total_text = price_total.get_text(strip=True) if price_total else ''
                
                price_avg = item.select_one('.property-price-average')
                price_avg_text = price_avg.get_text(strip=True) if price_avg else ''
                
                info = item.select_one('.property-content-info')
                info_text = info.get_text(strip=True) if info else ''
                
                address = item.select_one('.property-content-address')
                address_text = address.get_text(strip=True) if address else ''
                
                tags = []
                tag_elements = item.select('.property-content-tag span')
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    if tag_text:
                        tags.append(tag_text)
                
                detail_url_elem = item.select_one('a')
                detail_url = detail_url_elem['href'] if detail_url_elem and 'href' in detail_url_elem.attrs else ''
                
                total_price = float(re.search(r'(\d+(?:\.\d+)?)', price_total_text).group(1)) if re.search(r'(\d+(?:\.\d+)?)', price_total_text) else 0
                unit_price_val = float(re.search(r'(\d+)', price_avg_text).group(1)) if re.search(r'(\d+)', price_avg_text) else 0
                
                area_match = re.search(r'(\d+(?:\.\d+)?)㎡', info_text)
                area = float(area_match.group(1)) if area_match else 0
                
                if unit_price_val == 0 and total_price > 0 and area > 0:
                    unit_price_val = round(total_price * 10000 / area, 0)
                
                if not title or total_price == 0:
                    continue
                
                data = {
                    'title': title,
                    'district': district,
                    'location': address_text,
                    'total_price': total_price,
                    'unit_price': unit_price_val,
                    'area': area,
                    'house_type': '',
                    'tags': ','.join(tags),
                    'detail_url': detail_url,
                    'source': '安居客',
                    'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'insert_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'update_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                data_list.append(data)
            except Exception as e:
                logger.warning(f"解析安居客列表项失败: {e}")
        
        return data_list
    
    def get_anjuke_total_pages(self, html):
        """获取安居客总页数"""
        soup = BeautifulSoup(html, 'lxml')
        
        page_box = soup.select_one('.page-box')
        if page_box:
            try:
                page_info = page_box.get_text(strip=True)
                match = re.search(r'共(\d+)页', page_info)
                if match:
                    return int(match.group(1))
            except:
                pass
        
        page_links = soup.select('.page-box a')
        if page_links:
            try:
                last_page = page_links[-1].get_text(strip=True)
                if last_page.isdigit():
                    return int(last_page)
            except:
                pass
        
        return 20
    
    def crawl_anjuke(self):
        """爬取安居客"""
        logger.info("开始爬取安居客数据")
        
        district_urls = {
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
        
        for idx, (district, url) in enumerate(district_urls.items()):
            try:
                logger.info(f"[{idx+1}/{len(district_urls)}] 开始爬取 {district}")
                
                first_page_url = f"{url}p1/"
                html = self.get(first_page_url)
                
                if not html:
                    logger.warning(f"{district} 第1页获取失败")
                    continue
                
                if "antispam" in html.lower() or "captcha" in html.lower():
                    logger.warning(f"{district} 被反爬拦截")
                    continue
                
                total_pages = self.get_anjuke_total_pages(html)
                total_pages = min(total_pages, 50)
                
                logger.info(f"{district} 共 {total_pages} 页")
                
                data_list = self.parse_anjuke_list(html, district)
                if data_list:
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    logger.info(f"{district} 第1页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                
                for page in range(2, total_pages + 1):
                    page_url = f"{url}p{page}/"
                    html = self.get(page_url)
                    
                    if not html:
                        logger.warning(f"{district} 第{page}页获取失败")
                        continue
                    
                    data_list = self.parse_anjuke_list(html, district)
                    
                    if not data_list:
                        logger.info(f"{district} 第{page}页无数据，停止爬取")
                        break
                    
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    
                    logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                
                self.random_delay(3, 5)
                
            except Exception as e:
                logger.error(f"爬取安居客 {district} 失败: {e}")
        
        logger.info(f"安居客爬取完成，总数据量: {self.total_count}条")
    
    def parse_lianjia_list(self, html, district):
        """解析链家列表页"""
        soup = BeautifulSoup(html, 'lxml')
        items = soup.select('.sellListContent li')
        
        if not items:
            items = soup.select('.listContent li')
        
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
                
                if unit_price_val == 0 and total_price > 0 and area > 0:
                    unit_price_val = round(total_price * 10000 / area, 0)
                
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
                logger.warning(f"解析链家列表项失败: {e}")
        
        return data_list
    
    def get_lianjia_total_pages(self, html):
        """获取链家总页数"""
        soup = BeautifulSoup(html, 'lxml')
        
        page_box = soup.select_one('.page-box')
        if page_box:
            page_data = page_box.get('page-data')
            if page_data:
                try:
                    data = json.loads(page_data)
                    return data.get('totalPage', 100)
                except:
                    pass
        
        page_links = soup.select('.page-box a')
        if page_links:
            try:
                last_page = page_links[-2].get_text(strip=True)
                if last_page.isdigit():
                    return int(last_page)
            except:
                pass
        
        return 50
    
    def crawl_lianjia(self):
        """爬取链家"""
        logger.info("开始爬取链家数据")
        
        district_urls = {
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
        
        for idx, (district, url) in enumerate(district_urls.items()):
            try:
                logger.info(f"[{idx+1}/{len(district_urls)}] 开始爬取 {district}")
                
                first_page_url = f"{url}pg1/"
                html = self.get(first_page_url)
                
                if not html:
                    logger.warning(f"{district} 第1页获取失败")
                    continue
                
                if "login" in html.lower() or "auth" in html.lower():
                    logger.warning(f"{district} 需要登录")
                    continue
                
                total_pages = self.get_lianjia_total_pages(html)
                total_pages = min(total_pages, 50)
                
                logger.info(f"{district} 共 {total_pages} 页")
                
                data_list = self.parse_lianjia_list(html, district)
                if data_list:
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    logger.info(f"{district} 第1页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                
                for page in range(2, total_pages + 1):
                    page_url = f"{url}pg{page}/"
                    html = self.get(page_url)
                    
                    if not html:
                        logger.warning(f"{district} 第{page}页获取失败")
                        continue
                    
                    data_list = self.parse_lianjia_list(html, district)
                    
                    if not data_list:
                        logger.info(f"{district} 第{page}页无数据，停止爬取")
                        break
                    
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    
                    logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                
                self.random_delay(3, 5)
                
            except Exception as e:
                logger.error(f"爬取链家 {district} 失败: {e}")
        
        logger.info(f"链家爬取完成，总数据量: {self.total_count}条")
    
    def crawl(self, platforms=['anjuke', 'lianjia']):
        """爬取入口"""
        logger.info(f"开始爬取，平台: {platforms}")
        
        if 'anjuke' in platforms:
            self.crawl_anjuke()
        
        if 'lianjia' in platforms:
            self.crawl_lianjia()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='综合爬虫')
    parser.add_argument('--platform', choices=['anjuke', 'lianjia', 'both'], default='both', help='爬取平台')
    args = parser.parse_args()
    
    platforms = []
    if args.platform in ['anjuke', 'both']:
        platforms.append('anjuke')
    if args.platform in ['lianjia', 'both']:
        platforms.append('lianjia')
    
    spider = CombinedSpider()
    spider.crawl(platforms)
