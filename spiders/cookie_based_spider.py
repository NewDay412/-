import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import time
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from fake_useragent import UserAgent

class CookieBasedSpider:
    """基于Cookie的爬虫（先用浏览器获取Cookie，再用requests爬取）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.storage = CSVStorage()
        self.total_count = 0
        
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        })
        
        self.district_urls_anjuke = {
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
        
        self.district_urls_lianjia = {
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
    
    def get_cookies_from_browser(self, platform='anjuke'):
        """从浏览器获取Cookie"""
        logger.info(f"正在从浏览器获取{platform}的Cookie...")
        
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=' + self.ua.random)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        })
        
        try:
            if platform == 'anjuke':
                driver.get("https://chongqing.anjuke.com/sale/yuzhongqu/p1/")
            else:
                driver.get("https://cq.lianjia.com/ershoufang/yuzhong/pg1/")
            
            time.sleep(8)
            
            logger.info("请在浏览器中完成验证或登录，然后按 Enter 键继续...")
            input("")
            
            cookies = driver.get_cookies()
            
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            with open(f'{platform}_cookies.json', 'w', encoding='utf-8') as f:
                json.dump(cookie_dict, f, indent=2)
            
            logger.info(f"{platform} Cookie已获取并保存")
            
            self.session.cookies.update(cookie_dict)
            
        finally:
            driver.quit()
    
    def load_cookies(self, platform='anjuke'):
        """加载Cookie"""
        try:
            with open(f'{platform}_cookies.json', 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            self.session.cookies.update(cookies)
            logger.info(f"{platform} Cookie已加载")
            return True
        except:
            logger.info(f"未找到{platform} Cookie文件")
            return False
    
    def random_delay(self, min_sec=0.8, max_sec=1.8):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def get(self, url):
        """发送请求"""
        try:
            self.random_delay(0.8, 1.5)
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                logger.debug(f"请求成功: {url}")
                return response.text
            
            else:
                logger.warning(f"请求失败，状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
    
    def parse_anjuke(self, html, district):
        """解析安居客"""
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
    
    def crawl_anjuke(self):
        """爬取安居客"""
        logger.info("开始爬取安居客数据")
        
        for idx, (district, url) in enumerate(self.district_urls_anjuke.items()):
            try:
                logger.info(f"[{idx+1}/{len(self.district_urls_anjuke)}] 开始爬取 {district}")
                
                for page in range(1, 51):
                    page_url = f"{url}p{page}/"
                    html = self.get(page_url)
                    
                    if not html:
                        logger.warning(f"{district} 第{page}页获取失败")
                        continue
                    
                    if len(html) < 5000:
                        logger.warning(f"{district} 第{page}页内容过短，可能被反爬")
                        break
                    
                    data_list = self.parse_anjuke(html, district)
                    
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
    
    def parse_lianjia(self, html, district):
        """解析链家"""
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
                    tag_text = tag.get_text(strip=True) if tag_text else ''
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
    
    def crawl_lianjia(self):
        """爬取链家"""
        logger.info("开始爬取链家数据")
        
        for idx, (district, url) in enumerate(self.district_urls_lianjia.items()):
            try:
                logger.info(f"[{idx+1}/{len(self.district_urls_lianjia)}] 开始爬取 {district}")
                
                for page in range(1, 51):
                    page_url = f"{url}pg{page}/"
                    html = self.get(page_url)
                    
                    if not html:
                        logger.warning(f"{district} 第{page}页获取失败")
                        continue
                    
                    if "login" in html.lower() or "auth" in html.lower():
                        logger.warning(f"{district} 第{page}页需要登录")
                        break
                    
                    data_list = self.parse_lianjia(html, district)
                    
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
            if not self.load_cookies('anjuke'):
                self.get_cookies_from_browser('anjuke')
            self.crawl_anjuke()
        
        if 'lianjia' in platforms:
            if not self.load_cookies('lianjia'):
                self.get_cookies_from_browser('lianjia')
            self.crawl_lianjia()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='基于Cookie的爬虫')
    parser.add_argument('--platform', choices=['anjuke', 'lianjia', 'both'], default='both', help='爬取平台')
    args = parser.parse_args()
    
    platforms = []
    if args.platform in ['anjuke', 'both']:
        platforms.append('anjuke')
    if args.platform in ['lianjia', 'both']:
        platforms.append('lianjia')
    
    spider = CookieBasedSpider()
    spider.crawl(platforms)
