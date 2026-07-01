import time
from datetime import datetime, timedelta
from loguru import logger
from storage.mongodb import MongoDBStorage
from spiders.anjuke_spider import AnjukeSpider
from spiders.lianjia_spider import LianjiaSpider
from data_cleaning.cleaner import DataCleaner

class IncrementalUpdater:
    """增量更新模块"""
    
    def __init__(self):
        self.storage = MongoDBStorage()
        self.last_update_time = None
    
    def get_last_update_time(self):
        """获取上次更新时间"""
        try:
            result = self.storage.collection.find_one(
                {}, 
                {'update_time': 1, '_id': 0}
            ).sort('update_time', -1).limit(1)
            
            if result:
                self.last_update_time = result['update_time']
                logger.info(f"上次更新时间: {self.last_update_time}")
            else:
                self.last_update_time = datetime.now() - timedelta(days=30)
                logger.info("首次更新，默认上次更新时间为30天前")
            
            return self.last_update_time
        except Exception as e:
            logger.error(f"获取上次更新时间失败: {e}")
            self.last_update_time = datetime.now() - timedelta(days=30)
            return self.last_update_time
    
    def check_new_data(self):
        """检查是否有新数据"""
        logger.info("开始检查新数据")
        
        try:
            spider = AnjukeSpider()
            test_url = "https://chongqing.anjuke.com/sale/yuzhongqu/"
            response = spider.get(test_url)
            
            if response:
                logger.info("检测到网站可访问，开始增量更新")
                return True
            else:
                logger.warning("网站不可访问")
                return False
        except Exception as e:
            logger.error(f"检查新数据失败: {e}")
            return False
    
    def update(self):
        """执行增量更新"""
        logger.info("开始增量更新")
        
        if not self.check_new_data():
            logger.warning("无需更新")
            return
        
        self.get_last_update_time()
        
        try:
            spider = AnjukeSpider()
            spider.crawl()
            
            lianjia_spider = LianjiaSpider()
            lianjia_spider.crawl()
            
            cleaner = DataCleaner()
            cleaner.clean()
            
            logger.info("增量更新完成")
            
            return {
                'status': 'success',
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': '增量更新完成'
            }
        
        except Exception as e:
            logger.error(f"增量更新失败: {e}")
            return {
                'status': 'failed',
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'message': str(e)
            }
    
    def scheduled_update(self, interval_hours=24):
        """定时更新"""
        logger.info(f"定时更新已启动，间隔: {interval_hours}小时")
        
        while True:
            try:
                self.update()
                
                sleep_time = interval_hours * 3600
                logger.info(f"下次更新将在 {interval_hours} 小时后进行")
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"定时更新异常: {e}")
                time.sleep(3600)

if __name__ == "__main__":
    updater = IncrementalUpdater()
    
    result = updater.update()
    print(result)
    
    updater.storage.close()
