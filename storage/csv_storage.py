import pandas as pd
import os
from loguru import logger
from config import Config
from datetime import datetime

class CSVStorage:
    """CSV数据存储模块"""
    
    def __init__(self):
        self.data_dir = Config.SPIDER_SETTINGS["OUTPUT_DIR"]
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, "house_data.csv")
    
    def load_data(self):
        """加载数据"""
        if os.path.exists(self.file_path):
            df = pd.read_csv(self.file_path)
            logger.info(f"从CSV加载数据成功，共 {len(df)} 条")
            return df
        else:
            logger.info("CSV文件不存在，返回空DataFrame")
            return pd.DataFrame()
    
    def save_data(self, df):
        """保存数据"""
        df.to_csv(self.file_path, index=False, encoding='utf-8-sig')
        logger.info(f"数据保存成功，共 {len(df)} 条")
    
    def insert_one(self, data):
        """插入单条数据"""
        df = self.load_data()
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        self.save_data(df)
    
    def insert_many(self, data_list):
        """批量插入数据"""
        df = self.load_data()
        new_data = pd.DataFrame(data_list)
        df = pd.concat([df, new_data], ignore_index=True)
        self.save_data(df)
    
    def count_documents(self):
        """统计文档数量"""
        df = self.load_data()
        return len(df)
    
    def find(self, query=None, limit=None):
        """查询数据"""
        df = self.load_data()
        
        if query:
            for key, value in query.items():
                if key in df.columns:
                    df = df[df[key] == value]
        
        if limit:
            df = df.head(limit)
        
        return df.to_dict('records')
    
    def drop_collection(self):
        """删除数据"""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            logger.info("CSV数据已删除")
        else:
            logger.info("CSV文件不存在")

if __name__ == "__main__":
    storage = CSVStorage()
    print(f"当前数据量: {storage.count_documents()}")
