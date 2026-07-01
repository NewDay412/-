import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re
import time
import random
from loguru import logger
from config import Config
from storage.csv_storage import CSVStorage
from fake_useragent import UserAgent

class LianjiaSpiderFixed:
    """链家爬虫（修复版本）"""
    
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.storage = CSVStorage()
        self.total_count = 0
        self.driver = None
        self.ua = UserAgent()
    
    def init_driver(self, headless=False):
        """初始化浏览器"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=' + self.ua.random)
        chrome_options.add_argument('--accept-language=zh-CN,zh;q=0.9')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
        })
        
        self.driver.set_page_load_timeout(60)
        logger.info("浏览器驱动初始化成功")
    
    def close_driver(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            logger.info("浏览器驱动已关闭")
    
    def login_lianjia(self):
        """登录链家"""
        if not self.username or not self.password:
            logger.error("请提供链家账号密码")
            return False
        
        try:
            logger.info("开始登录链家")
            self.driver.get("https://clogin.lianjia.com/login/")
            time.sleep(5)
            
            try:
                phone_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "phone"))
                )
            except:
                try:
                    phone_input = self.driver.find_element(By.XPATH, '//input[@placeholder="手机号"]')
                except:
                    try:
                        phone_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="tel"]')
                    except:
                        logger.error("未找到手机号输入框")
                        return False
            
            phone_input.clear()
            phone_input.send_keys(self.username)
            time.sleep(1)
            
            try:
                password_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "password"))
                )
            except:
                try:
                    password_input = self.driver.find_element(By.XPATH, '//input[@placeholder="密码"]')
                except:
                    try:
                        password_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
                    except:
                        logger.error("未找到密码输入框")
                        return False
            
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)
            
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-primary")
            except:
                try:
                    login_btn = self.driver.find_element(By.XPATH, '//button[contains(text(),"登录")]')
                except:
                    logger.error("未找到登录按钮")
                    return False
            
            login_btn.click()
            time.sleep(10)
            
            current_url = self.driver.current_url.lower()
            if "login" not in current_url:
                logger.info("链家登录成功")
                return True
            else:
                logger.error("链家登录失败，请检查账号密码")
                logger.error(f"当前URL: {self.driver.current_url}")
                return False
                
        except Exception as e:
            logger.error(f"链家登录异常: {e}")
            return False
    
    def parse_page(self, html, district):
        """解析页面"""
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
                logger.warning(f"解析列表项失败: {e}")
        
        return data_list
    
    def crawl(self):
        """爬取入口"""
        logger.info("开始爬取链家数据")
        
        self.init_driver(headless=False)
        
        try:
            self.driver.get("https://cq.lianjia.com/ershoufang/yuzhong/pg1/")
            time.sleep(5)
            
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "auth" in current_url:
                logger.info("链家需要登录，尝试登录...")
                if not self.login_lianjia():
                    logger.error("登录失败，无法爬取链家数据")
                    return
            
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
                    
                    page = 1
                    max_pages = 50
                    has_data = True
                    consecutive_failures = 0
                    
                    while page <= max_pages and has_data and consecutive_failures < 3:
                        page_url = f"{url}pg{page}/"
                        logger.info(f"正在爬取 {district} 第{page}页: {page_url}")
                        
                        self.driver.get(page_url)
                        time.sleep(random.uniform(3, 5))
                        
                        current_url = self.driver.current_url.lower()
                        if "login" in current_url or "auth" in current_url:
                            logger.warning(f"{district} 第{page}页被重定向到登录页")
                            consecutive_failures += 1
                            if not self.login_lianjia():
                                break
                            continue
                        
                        html = self.driver.page_source
                        data_list = self.parse_page(html, district)
                        
                        if not data_list:
                            consecutive_failures += 1
                            logger.info(f"{district} 第{page}页无数据，连续失败: {consecutive_failures}")
                            
                            if consecutive_failures >= 3:
                                logger.info(f"{district} 连续3页无数据，停止爬取")
                                has_data = False
                                break
                            
                            time.sleep(random.uniform(5, 10))
                            continue
                        
                        consecutive_failures = 0
                        
                        self.storage.insert_many(data_list)
                        self.total_count += len(data_list)
                        
                        logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                        
                        page += 1
                        time.sleep(random.uniform(2, 4))
                    
                    time.sleep(random.uniform(3, 5))
                    
                except Exception as e:
                    logger.error(f"爬取 {district} 失败: {e}")
            
            logger.info(f"链家爬取完成，总数据量: {self.total_count}条")
            
        finally:
            self.close_driver()

if __name__ == "__main__":
    import getpass
    
    print("=" * 60)
    print("链家二手房数据爬虫")
    print("=" * 60)
    
    username = input("请输入链家账号（手机号）: ").strip()
    password = getpass.getpass("请输入链家密码: ").strip()
    
    spider = LianjiaSpiderFixed(username, password)
    spider.crawl()
