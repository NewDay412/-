import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from config import Config
from loguru import logger
import time
import random
from threading import Lock

class BaseSpider:
    """爬虫基类"""
    
    def __init__(self, name):
        self.name = name
        self.session = requests.Session()
        self.ua = UserAgent()
        self.lock = Lock()
        
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
    
    def get(self, url, params=None, headers=None, retry=Config.SPIDER_SETTINGS["MAX_RETRIES"]):
        """发送GET请求"""
        try:
            if headers:
                self.session.headers.update(headers)
            
            time.sleep(random.uniform(1, Config.SPIDER_SETTINGS["REQUEST_DELAY"]))
            
            response = self.session.get(
                url,
                params=params,
                timeout=Config.SPIDER_SETTINGS["TIMEOUT"],
                verify=False
            )
            
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            logger.debug(f"请求成功: {url}")
            return response
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"请求失败: {url}, 错误: {e}")
            
            if retry > 0:
                logger.info(f"重试第 {Config.SPIDER_SETTINGS['MAX_RETRIES'] - retry + 1} 次...")
                time.sleep(random.uniform(3, 5))
                return self.get(url, params, headers, retry - 1)
            else:
                logger.error(f"请求失败，已达最大重试次数: {url}")
                raise
    
    def post(self, url, data=None, json=None, headers=None, retry=Config.SPIDER_SETTINGS["MAX_RETRIES"]):
        """发送POST请求"""
        try:
            if headers:
                self.session.headers.update(headers)
            
            time.sleep(random.uniform(1, Config.SPIDER_SETTINGS["REQUEST_DELAY"]))
            
            response = self.session.post(
                url,
                data=data,
                json=json,
                timeout=Config.SPIDER_SETTINGS["TIMEOUT"],
                verify=False
            )
            
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            logger.debug(f"POST请求成功: {url}")
            return response
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"POST请求失败: {url}, 错误: {e}")
            
            if retry > 0:
                logger.info(f"重试第 {Config.SPIDER_SETTINGS['MAX_RETRIES'] - retry + 1} 次...")
                time.sleep(random.uniform(3, 5))
                return self.post(url, data, json, headers, retry - 1)
            else:
                logger.error(f"POST请求失败，已达最大重试次数: {url}")
                raise
    
    def parse_html(self, html):
        """解析HTML"""
        try:
            return BeautifulSoup(html, 'lxml')
        except Exception as e:
            logger.error(f"HTML解析失败: {e}")
            raise
    
    def extract_text(self, element, default=""):
        """提取元素文本"""
        if element:
            return element.get_text(strip=True)
        return default
    
    def extract_attr(self, element, attr, default=""):
        """提取元素属性"""
        if element and attr in element.attrs:
            return element[attr]
        return default
    
    def save_data(self, data_list):
        """保存数据（需子类实现）"""
        raise NotImplementedError("子类必须实现save_data方法")
    
    def crawl(self):
        """爬取入口（需子类实现）"""
        raise NotImplementedError("子类必须实现crawl方法")
    
    def random_headers(self):
        """生成随机请求头"""
        return {
            'User-Agent': self.ua.random,
            'Referer': 'https://www.baidu.com/'
        }
    
    def close(self):
        """关闭会话"""
        self.session.close()
        logger.info(f"{self.name}爬虫会话已关闭")

if __name__ == "__main__":
    spider = BaseSpider("测试爬虫")
    response = spider.get("http://httpbin.org/headers")
    print(response.text)
    spider.close()
