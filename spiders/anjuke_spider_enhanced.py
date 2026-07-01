import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import re
import time
import random
import json
import requests
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from fake_useragent import UserAgent

class AnjukeEnhancedSpider:
    """安居客增强版爬虫（处理网易易盾验证码）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.storage = CSVStorage()
        self.total_count = 0
        self.driver = None
        self.session = requests.Session()
        
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
    
    def init_driver(self, headless=False):
        """初始化浏览器（增强反检测）"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        random_user_agent = self.ua.random
        chrome_options.add_argument(f'--user-agent={random_user_agent}')
        chrome_options.add_argument('--accept-language=zh-CN,zh;q=0.9,en;q=0.8')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,
                'javascript': 1,
                'plugins': 2,
                'popups': 2,
                'geolocation': 2,
                'notifications': 2,
                'auto_select_certificate': 2,
                'fullscreen': 2,
                'mouselock': 2,
                'mixed_script': 2,
                'media_stream': 2,
                'media_stream_mic': 2,
                'media_stream_camera': 2,
                'protocol_handlers': 2,
                'ppapi_broker': 2,
                'automatic_downloads': 2,
                'midi_sysex': 2,
                'push_messaging': 2,
                'ssl_cert_decisions': 2,
                'metro_switch_to_desktop': 2,
                'protected_media_identifier': 2,
                'app_banner': 2,
                'site_engagement': 2,
                'durable_storage': 2
            }
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
                Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => Math.floor(Math.random() * 4) + 4 });
                Object.defineProperty(navigator, 'deviceMemory', { get: () => Math.floor(Math.random() * 4) + 4 });
                window.chrome = { runtime: {} };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            '''
        })
        
        self.driver.set_page_load_timeout(60)
        logger.info(f"浏览器驱动初始化成功，UA: {random_user_agent[:50]}...")
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器驱动已关闭")
    
    def random_delay(self, min_sec=1, max_sec=3):
        """随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def simulate_human_behavior(self):
        """模拟人类行为"""
        try:
            scroll_height = self.driver.execute_script('return document.body.scrollHeight')
            for _ in range(random.randint(3, 6)):
                scroll_amount = random.uniform(100, 400)
                self.driver.execute_script(f'window.scrollBy(0, {scroll_amount})')
                self.random_delay(0.2, 0.8)
            
            self.driver.execute_script('window.scrollTo(0, 0)')
            self.random_delay(0.5, 1)
            
            action = ActionChains(self.driver)
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                action.move_by_offset(x, y).pause(random.uniform(0.1, 0.4))
            action.perform()
            
        except Exception as e:
            logger.warning(f"模拟人类行为失败: {e}")
    
    def is_yidun_captcha(self):
        """检测是否为网易易盾验证码"""
        page_source = self.driver.page_source.lower()
        
        if 'yidun' in page_source or 'captcha-wy' in page_source:
            return True
        
        if '易盾' in self.driver.title or '验证' in self.driver.title:
            return True
        
        if 'esfcommon-captcha' in self.driver.current_url.lower():
            return True
        
        return False
    
    def is_blocked(self):
        """检测是否被反爬拦截"""
        current_url = self.driver.current_url.lower()
        page_source = self.driver.page_source.lower()
        
        if self.is_yidun_captcha():
            return True
        
        if 'antispam' in current_url or 'verify' in current_url or 'captcha' in current_url:
            return True
        
        if '请验证您是真人' in page_source or '人机验证' in page_source or '安全验证' in page_source:
            return True
        
        if 'antispam' in page_source or 'captcha' in page_source:
            return True
        
        return False
    
    def handle_block(self):
        """处理反爬拦截"""
        logger.warning("检测到反爬拦截，请在浏览器中完成验证")
        logger.info("验证完成后按 Enter 键继续...")
        
        try:
            input("")
            logger.info("验证完成，继续爬取...")
            return True
        except:
            logger.error("验证超时或取消")
            return False
    
    def save_cookies(self):
        """保存Cookie"""
        cookies = self.driver.get_cookies()
        with open('anjuke_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f)
        logger.info("Cookie已保存")
    
    def load_cookies(self):
        """加载Cookie"""
        try:
            with open('anjuke_cookies.json', 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            logger.info("Cookie已加载")
        except:
            logger.info("未找到Cookie文件")
    
    def get_page(self, url):
        """获取页面（带反爬处理）"""
        try:
            self.driver.get(url)
            self.random_delay(4, 6)
            
            if self.is_blocked():
                if not self.handle_block():
                    return None
            
            self.simulate_human_behavior()
            
            return self.driver.page_source
            
        except TimeoutException:
            logger.warning(f"页面加载超时: {url}")
            return None
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return None
    
    def parse_page(self, html, district):
        """解析页面"""
        soup = BeautifulSoup(html, 'lxml')
        
        items = soup.select('.property-ex')
        if not items:
            items = soup.select('.list-item')
        if not items:
            items = soup.select('.item')
        if not items:
            items = soup.select('[class*="property"]')
        if not items:
            items = soup.select('div[class*="house"]')
        
        data_list = []
        
        for item in items:
            try:
                title_elem = item.select_one('.property-content-title-name') or item.select_one('.title a') or item.select_one('h2 a')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                price_total = item.select_one('.property-price-total') or item.select_one('.price') or item.select_one('.totalPrice')
                price_total_text = price_total.get_text(strip=True) if price_total else ''
                
                price_avg = item.select_one('.property-price-average') or item.select_one('.unit-price') or item.select_one('.unitPrice')
                price_avg_text = price_avg.get_text(strip=True) if price_avg else ''
                
                info = item.select_one('.property-content-info') or item.select_one('.info') or item.select_one('.houseInfo')
                info_text = info.get_text(strip=True) if info else ''
                
                address = item.select_one('.property-content-address') or item.select_one('.address') or item.select_one('.positionInfo')
                address_text = address.get_text(strip=True) if address else ''
                
                tags = []
                tag_elements = item.select('.property-content-tag span') or item.select('.tag') or item.select('.tags span')
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
    
    def crawl(self):
        """爬取入口"""
        logger.info("开始爬取安居客数据（增强版）")
        
        self.init_driver(headless=False)
        
        try:
            self.driver.get("https://chongqing.anjuke.com/")
            self.random_delay(8, 12)
            
            self.load_cookies()
            
            if self.is_blocked():
                if not self.handle_block():
                    return
            
            self.save_cookies()
            
            for idx, (district, url) in enumerate(self.district_urls.items()):
                try:
                    logger.info(f"[{idx+1}/{len(self.district_urls)}] 开始爬取 {district}")
                    
                    page = 1
                    max_pages = 50
                    has_data = True
                    consecutive_failures = 0
                    
                    while page <= max_pages and has_data and consecutive_failures < 3:
                        page_url = f"{url}p{page}/"
                        logger.info(f"正在爬取 {district} 第{page}页: {page_url}")
                        
                        html = self.get_page(page_url)
                        
                        if not html:
                            consecutive_failures += 1
                            logger.warning(f"{district} 第{page}页获取失败，连续失败: {consecutive_failures}")
                            self.random_delay(8, 15)
                            continue
                        
                        data_list = self.parse_page(html, district)
                        
                        if not data_list:
                            consecutive_failures += 1
                            logger.info(f"{district} 第{page}页无数据，连续失败: {consecutive_failures}")
                            
                            if consecutive_failures >= 3:
                                logger.info(f"{district} 连续3页无数据，停止爬取")
                                has_data = False
                                break
                            
                            self.random_delay(8, 15)
                            continue
                        
                        consecutive_failures = 0
                        
                        self.storage.insert_many(data_list)
                        self.total_count += len(data_list)
                        
                        logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                        
                        page += 1
                        
                        if page % 5 == 0:
                            logger.info("保存Cookie...")
                            self.save_cookies()
                            self.random_delay(8, 15)
                        else:
                            self.random_delay(3, 6)
                    
                    self.random_delay(5, 8)
                    
                except Exception as e:
                    logger.error(f"爬取 {district} 失败: {e}")
                    self.random_delay(8, 15)
            
            self.save_cookies()
            logger.info(f"安居客爬取完成，总数据量: {self.total_count}条")
            
        finally:
            self.close_driver()

if __name__ == "__main__":
    spider = AnjukeEnhancedSpider()
    spider.crawl()
