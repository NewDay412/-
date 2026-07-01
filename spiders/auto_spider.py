import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
import time
import random
import json
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from fake_useragent import UserAgent

class AutoSpider:
    """全自动爬虫（使用Selenium处理反爬）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.storage = CSVStorage()
        self.total_count = 0
        self.driver = None
        
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
    
    def init_driver(self):
        """初始化浏览器"""
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=' + self.ua.random)
        chrome_options.add_argument('--accept-language=zh-CN,zh;q=0.9')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            '''
        })
        
        self.driver.set_page_load_timeout(60)
        logger.info("浏览器驱动初始化成功")
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器驱动已关闭")
    
    def random_delay(self, min_sec=1, max_sec=3):
        """随机延迟"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def simulate_human(self):
        """模拟人类行为"""
        try:
            for _ in range(random.randint(2, 4)):
                scroll_amount = random.uniform(100, 300)
                self.driver.execute_script(f'window.scrollBy(0, {scroll_amount})')
                self.random_delay(0.3, 0.8)
            
            self.driver.execute_script('window.scrollTo(0, 0)')
            self.random_delay(0.5, 1)
            
            action = ActionChains(self.driver)
            for _ in range(random.randint(2, 3)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                action.move_by_offset(x, y).pause(random.uniform(0.1, 0.3))
            action.perform()
        except:
            pass
    
    def is_blocked(self):
        """检测是否被反爬拦截"""
        page_source = self.driver.page_source.lower()
        
        if 'yidun' in page_source or 'captcha-wy' in page_source:
            return True
        
        if '请验证您是真人' in page_source or '人机验证' in page_source:
            return True
        
        if 'antispam' in page_source or 'captcha' in page_source:
            return True
        
        return False
    
    def parse_anjuke(self, html, district):
        """解析安居客"""
        soup = BeautifulSoup(html, 'lxml')
        items = soup.select('.property-ex')
        
        if not items:
            items = soup.select('.list-item')
        if not items:
            items = soup.select('[class*="property"]')
        
        data_list = []
        
        for item in items:
            try:
                title_elem = item.select_one('.property-content-title-name') or item.select_one('.title a')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                price_total = item.select_one('.property-price-total') or item.select_one('.price')
                price_total_text = price_total.get_text(strip=True) if price_total else ''
                
                price_avg = item.select_one('.property-price-average') or item.select_one('.unit-price')
                price_avg_text = price_avg.get_text(strip=True) if price_avg else ''
                
                info = item.select_one('.property-content-info') or item.select_one('.info')
                info_text = info.get_text(strip=True) if info else ''
                
                address = item.select_one('.property-content-address') or item.select_one('.address')
                address_text = address.get_text(strip=True) if address else ''
                
                tags = []
                tag_elements = item.select('.property-content-tag span') or item.select('.tag')
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
                logger.warning(f"解析列表项失败: {e}")
        
        return data_list
    
    def crawl_anjuke(self):
        """爬取安居客"""
        logger.info("开始爬取安居客数据")
        
        try:
            self.driver.get("https://chongqing.anjuke.com/")
            self.random_delay(5, 8)
            
            if self.is_blocked():
                logger.warning("检测到反爬拦截，等待用户手动验证...")
                self.random_delay(30, 60)
                
                if self.is_blocked():
                    logger.error("验证超时，无法继续爬取")
                    return
            
            for idx, (district, url) in enumerate(self.district_urls_anjuke.items()):
                try:
                    logger.info(f"[{idx+1}/{len(self.district_urls_anjuke)}] 开始爬取 {district}")
                    
                    for page in range(1, 51):
                        page_url = f"{url}p{page}/"
                        logger.info(f"正在爬取 {district} 第{page}页")
                        
                        self.driver.get(page_url)
                        self.random_delay(4, 6)
                        
                        if self.is_blocked():
                            logger.warning(f"{district} 第{page}页被拦截")
                            self.random_delay(30, 60)
                            
                            if self.is_blocked():
                                logger.warning(f"{district} 验证超时，跳过")
                                break
                        
                        self.simulate_human()
                        
                        html = self.driver.page_source
                        data_list = self.parse_anjuke(html, district)
                        
                        if not data_list:
                            logger.info(f"{district} 第{page}页无数据，停止爬取")
                            break
                        
                        self.storage.insert_many(data_list)
                        self.total_count += len(data_list)
                        
                        logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                        
                        if page % 5 == 0:
                            self.random_delay(8, 12)
                        else:
                            self.random_delay(2, 4)
                    
                    self.random_delay(3, 5)
                    
                except Exception as e:
                    logger.error(f"爬取 {district} 失败: {e}")
            
            logger.info(f"安居客爬取完成，总数据量: {self.total_count}条")
            
        except Exception as e:
            logger.error(f"爬取安居客失败: {e}")
    
    def crawl(self):
        """爬取入口"""
        logger.info("开始全自动爬取")
        
        self.init_driver()
        
        try:
            self.crawl_anjuke()
        finally:
            self.close_driver()

if __name__ == "__main__":
    spider = AutoSpider()
    spider.crawl()
