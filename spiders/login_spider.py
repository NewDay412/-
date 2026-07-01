import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

class LoginSpider:
    """支持登录的爬虫（链家+安居客）"""
    
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.storage = CSVStorage()
        self.total_count = 0
        self.driver = None
    
    def init_driver(self, headless=False):
        """初始化浏览器"""
        chrome_options = Options()
        if headless:
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
    
    def login_lianjia(self):
        """登录链家"""
        if not self.username or not self.password:
            logger.error("请提供链家账号密码")
            return False
        
        try:
            logger.info("开始登录链家")
            self.driver.get("https://clogin.lianjia.com/login/")
            time.sleep(3)
            
            phone_input = self.driver.find_element(By.NAME, "phone")
            phone_input.clear()
            phone_input.send_keys(self.username)
            time.sleep(1)
            
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)
            
            login_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-primary")
            login_btn.click()
            time.sleep(5)
            
            if "login" not in self.driver.current_url.lower():
                logger.info("链家登录成功")
                return True
            else:
                logger.error("链家登录失败，请检查账号密码")
                return False
                
        except Exception as e:
            logger.error(f"链家登录异常: {e}")
            return False
    
    def login_anjuke(self):
        """登录安居客"""
        if not self.username or not self.password:
            logger.error("请提供安居客账号密码")
            return False
        
        try:
            logger.info("开始登录安居客")
            self.driver.get("https://user.anjuke.com/login/")
            time.sleep(3)
            
            phone_input = self.driver.find_element(By.NAME, "phone")
            phone_input.clear()
            phone_input.send_keys(self.username)
            time.sleep(1)
            
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(self.password)
            time.sleep(1)
            
            login_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-submit")
            login_btn.click()
            time.sleep(5)
            
            if "login" not in self.driver.current_url.lower():
                logger.info("安居客登录成功")
                return True
            else:
                logger.error("安居客登录失败，请检查账号密码")
                return False
                
        except Exception as e:
            logger.error(f"安居客登录异常: {e}")
            return False
    
    def test_login_required(self, platform="lianjia"):
        """测试是否需要登录"""
        logger.info(f"测试{platform}是否需要登录")
        self.init_driver(headless=True)
        
        try:
            if platform == "lianjia":
                self.driver.get("https://cq.lianjia.com/ershoufang/yuzhong/pg1/")
            else:
                self.driver.get("https://chongqing.anjuke.com/sale/yuzhongqu/p1/")
            
            time.sleep(5)
            current_url = self.driver.current_url
            
            if "login" in current_url.lower() or "auth" in current_url.lower():
                logger.info(f"{platform}需要登录，当前URL: {current_url}")
                self.close_driver()
                return True
            else:
                logger.info(f"{platform}不需要登录，当前URL: {current_url}")
                self.close_driver()
                return False
                
        except Exception as e:
            logger.error(f"测试登录需求异常: {e}")
            self.close_driver()
            return True
    
    def parse_lianjia_page(self, html, district):
        """解析链家页面"""
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
                logger.warning(f"解析链家列表项失败: {e}")
        
        return data_list
    
    def crawl_lianjia(self, headless=False):
        """爬取链家"""
        logger.info("开始爬取链家数据")
        
        if not self.driver:
            self.init_driver(headless=headless)
        
        if self.test_login_required("lianjia"):
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
        
        for district, url in district_urls.items():
            try:
                page = 1
                max_pages = 50
                has_data = True
                
                while page <= max_pages and has_data:
                    page_url = f"{url}pg{page}/"
                    logger.info(f"正在爬取链家 {district} 第{page}页: {page_url}")
                    
                    self.driver.get(page_url)
                    time.sleep(random.uniform(3, 5))
                    
                    html = self.driver.page_source
                    data_list = self.parse_lianjia_page(html, district)
                    
                    if not data_list:
                        logger.info(f"{district} 第{page}页无数据，停止爬取")
                        has_data = False
                        break
                    
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    
                    logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                    
                    page += 1
                    time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"爬取链家 {district} 失败: {e}")
        
        logger.info(f"链家爬取完成，总数据量: {self.total_count}条")
    
    def parse_anjuke_page(self, html, district):
        """解析安居客页面"""
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
                
                detail_url = item.select_one('.property-content-title-name')
                detail_url = detail_url['href'] if detail_url and 'href' in detail_url.attrs else ''
                
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
    
    def crawl_anjuke(self, headless=False):
        """爬取安居客"""
        logger.info("开始爬取安居客数据")
        
        if not self.driver:
            self.init_driver(headless=headless)
        
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
        
        for district, url in district_urls.items():
            try:
                page = 1
                max_pages = 50
                has_data = True
                
                while page <= max_pages and has_data:
                    page_url = f"{url}p{page}/"
                    logger.info(f"正在爬取安居客 {district} 第{page}页: {page_url}")
                    
                    self.driver.get(page_url)
                    time.sleep(random.uniform(3, 5))
                    
                    html = self.driver.page_source
                    
                    if "antispam" in self.driver.current_url.lower():
                        logger.warning(f"{district} 被反爬拦截，请手动验证后继续")
                        input("完成验证后按 Enter 键继续...")
                        html = self.driver.page_source
                    
                    data_list = self.parse_anjuke_page(html, district)
                    
                    if not data_list:
                        logger.info(f"{district} 第{page}页无数据，停止爬取")
                        has_data = False
                        break
                    
                    self.storage.insert_many(data_list)
                    self.total_count += len(data_list)
                    
                    logger.info(f"{district} 第{page}页完成，本次: {len(data_list)}条，累计: {self.total_count}条")
                    
                    page += 1
                    time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"爬取安居客 {district} 失败: {e}")
        
        logger.info(f"安居客爬取完成，总数据量: {self.total_count}条")

def main():
    """主函数"""
    import argparse
    import getpass
    
    parser = argparse.ArgumentParser(description='重庆市二手房数据爬虫')
    parser.add_argument('--platform', choices=['lianjia', 'anjuke', 'both'], default='both', help='爬取平台')
    parser.add_argument('--username', help='链家账号（手机号）')
    parser.add_argument('--password', help='链家密码')
    parser.add_argument('--headless', action='store_true', help='无头模式运行')
    args = parser.parse_args()
    
    print("=" * 60)
    print("重庆市二手房数据爬虫")
    print("=" * 60)
    print()
    
    username = args.username
    password = args.password
    
    if args.platform in ['lianjia', 'both']:
        if not username:
            username = input("请输入链家账号（手机号）: ").strip()
        if not password:
            password = getpass.getpass("请输入链家密码: ").strip()
    
    spider = LoginSpider(username, password)
    
    try:
        if args.platform in ['lianjia', 'both']:
            spider.crawl_lianjia(headless=args.headless)
        
        if args.platform in ['anjuke', 'both']:
            spider.crawl_anjuke(headless=args.headless)
            
    finally:
        spider.close_driver()

if __name__ == "__main__":
    main()
