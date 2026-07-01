import pymongo
from pymongo import MongoClient
from config import Config
from loguru import logger
import pandas as pd
import os
from datetime import datetime

class MongoDBStorage:
    """MongoDB数据存储模块"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """连接MongoDB数据库"""
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.MONGODB_DB]
            self.collection = self.db[Config.MONGODB_COLLECTION]
            self.client.admin.command('ping')
            logger.info("MongoDB连接成功")
        except Exception as e:
            logger.error(f"MongoDB连接失败: {e}")
            raise
    
    def insert_one(self, data):
        """插入单条数据"""
        if not isinstance(data, dict):
            logger.error("数据类型必须为dict")
            raise TypeError("数据类型必须为dict")
        
        data['insert_time'] = datetime.now()
        data['update_time'] = datetime.now()
        
        try:
            result = self.collection.insert_one(data)
            logger.debug(f"插入数据成功，ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            raise
    
    def insert_many(self, data_list):
        """批量插入数据"""
        if not isinstance(data_list, list):
            logger.error("数据类型必须为list")
            raise TypeError("数据类型必须为list")
        
        for data in data_list:
            data['insert_time'] = datetime.now()
            data['update_time'] = datetime.now()
        
        try:
            result = self.collection.insert_many(data_list)
            logger.info(f"批量插入数据成功，数量: {len(result.inserted_ids)}")
            return result.inserted_ids
        except Exception as e:
            logger.error(f"批量插入数据失败: {e}")
            raise
    
    def update_one(self, query, update_data):
        """更新单条数据"""
        update_data['update_time'] = datetime.now()
        
        try:
            result = self.collection.update_one(query, {'$set': update_data})
            if result.modified_count > 0:
                logger.debug(f"更新数据成功，匹配: {result.matched_count}, 修改: {result.modified_count}")
            return result
        except Exception as e:
            logger.error(f"更新数据失败: {e}")
            raise
    
    def find_one(self, query):
        """查询单条数据"""
        try:
            return self.collection.find_one(query)
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            raise
    
    def find(self, query=None, projection=None, limit=None, skip=None):
        """查询多条数据"""
        try:
            cursor = self.collection.find(query, projection)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            raise
    
    def count_documents(self, query=None):
        """统计文档数量"""
        try:
            return self.collection.count_documents(query or {})
        except Exception as e:
            logger.error(f"统计文档数量失败: {e}")
            raise
    
    def create_index(self, field, unique=False):
        """创建索引"""
        try:
            self.collection.create_index(field, unique=unique)
            logger.info(f"创建索引成功: {field}")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise
    
    def drop_collection(self):
        """删除集合"""
        try:
            self.collection.drop()
            logger.info("删除集合成功")
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            raise
    
    def export_to_csv(self, file_path=None):
        """导出数据到CSV文件"""
        if file_path is None:
            os.makedirs(Config.SPIDER_SETTINGS["OUTPUT_DIR"], exist_ok=True)
            file_path = os.path.join(Config.SPIDER_SETTINGS["OUTPUT_DIR"], 
                                     f"house_data_{datetime.now().strftime('%Y%m%d')}.csv")
        
        try:
            data = list(self.collection.find({}, {'_id': 0}))
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            logger.info(f"数据导出成功，文件路径: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            raise
    
    def export_to_excel(self, file_path=None):
        """导出数据到Excel文件"""
        if file_path is None:
            os.makedirs(Config.SPIDER_SETTINGS["OUTPUT_DIR"], exist_ok=True)
            file_path = os.path.join(Config.SPIDER_SETTINGS["OUTPUT_DIR"], 
                                     f"house_data_{datetime.now().strftime('%Y%m%d')}.xlsx")
        
        try:
            data = list(self.collection.find({}, {'_id': 0}))
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            logger.info(f"数据导出成功，文件路径: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            raise
    
    def check_duplicate(self, unique_key, value):
        """检查数据是否重复"""
        try:
            count = self.collection.count_documents({unique_key: value})
            return count > 0
        except Exception as e:
            logger.error(f"检查重复数据失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            logger.info("MongoDB连接已关闭")

if __name__ == "__main__":
    storage = MongoDBStorage()
    print(f"当前数据量: {storage.count_documents()}")
    
    test_data = {
        "title": "测试房源",
        "district": "渝中区",
        "price": 15000,
        "area": 80,
        "source": "test"
    }
    
    storage.insert_one(test_data)
    print(f"插入后数据量: {storage.count_documents()}")
    
    storage.close()
