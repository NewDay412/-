import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from loguru import logger
from storage.csv_storage import CSVStorage
from config import Config
import re
from datetime import datetime

class DataCleaner:
    """数据清洗模块"""
    
    def __init__(self, use_csv=True):
        self.use_csv = use_csv
        if use_csv:
            self.storage = CSVStorage()
        else:
            from storage.mongodb import MongoDBStorage
            self.storage = MongoDBStorage()
    
    def load_data(self):
        """加载数据"""
        logger.info("开始加载数据")
        if self.use_csv:
            df = self.storage.load_data()
        else:
            data = self.storage.find({}, {'_id': 0})
            df = pd.DataFrame(data)
        logger.info(f"加载数据完成，共 {len(df)} 条")
        return df
    
    def remove_duplicates(self, df):
        """去除重复数据"""
        initial_count = len(df)
        df = df.drop_duplicates(subset=['title', 'district', 'area', 'total_price'], keep='first')
        removed_count = initial_count - len(df)
        logger.info(f"去除重复数据: {removed_count} 条")
        return df
    
    def handle_missing_values(self, df):
        """处理缺失值"""
        logger.info("开始处理缺失值")
        
        missing_info = df.isnull().sum()
        logger.info(f"缺失值统计:\n{missing_info}")
        
        df = df.dropna(subset=['title', 'district', 'total_price'])
        
        df['area'] = df['area'].fillna(df['area'].median())
        df['unit_price'] = df['unit_price'].fillna(df['unit_price'].median())
        df['location'] = df['location'].fillna('未知')
        
        logger.info(f"处理缺失值后，数据量: {len(df)}")
        return df
    
    def validate_data(self, df):
        """验证数据有效性"""
        logger.info("开始验证数据有效性")
        
        df = df[df['total_price'] > 0]
        df = df[df['area'] > 0]
        df = df[df['unit_price'] > 0]
        
        df = df[df['area'] < 1000]
        df = df[df['total_price'] < 10000]
        df = df[df['unit_price'] < 50000]
        
        district_set = set(Config.CHONGQING_DISTRICTS)
        df = df[df['district'].isin(district_set)]
        
        logger.info(f"验证数据有效性后，数据量: {len(df)}")
        return df
    
    def extract_features(self, df):
        """提取特征"""
        logger.info("开始提取特征")
        
        df['price_per_sqm'] = df['unit_price']
        
        df['house_type'] = df['title'].apply(
            lambda x: re.search(r'(\d+)室(\d+)厅', str(x)).group() 
            if re.search(r'(\d+)室(\d+)厅', str(x)) else '未知户型'
        )
        
        df['floor_info'] = df['title'].apply(
            lambda x: '高层' if '高' in str(x) else '中层' if '中' in str(x) else '低层' if '低' in str(x) else '未知楼层'
        )
        
        df['year_info'] = df['title'].apply(
            lambda x: int(re.search(r'(\d{4})年', str(x)).group(1)) 
            if re.search(r'(\d{4})年', str(x)) else np.nan
        )
        
        df['year_info'] = df['year_info'].fillna(df['year_info'].median().astype(int))
        
        logger.info("特征提取完成")
        return df
    
    def clean(self):
        """执行完整清洗流程"""
        logger.info("开始数据清洗")
        
        df = self.load_data()
        
        if len(df) == 0:
            logger.warning("没有数据需要清洗")
            return None
        
        df = self.remove_duplicates(df)
        df = self.handle_missing_values(df)
        df = self.validate_data(df)
        df = self.extract_features(df)
        
        df['clean_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.storage.drop_collection()
        
        data_dict = df.to_dict('records')
        self.storage.insert_many(data_dict)
        
        logger.info(f"数据清洗完成，清洗后数据量: {len(df)}")
        
        return df
    
    def save_cleaned_data(self, df, file_path=None):
        """保存清洗后的数据"""
        if file_path is None:
            import os
            os.makedirs(Config.SPIDER_SETTINGS["OUTPUT_DIR"], exist_ok=True)
            file_path = os.path.join(Config.SPIDER_SETTINGS["OUTPUT_DIR"], 
                                     f"cleaned_house_data_{datetime.now().strftime('%Y%m%d')}.csv")
        
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        logger.info(f"清洗后数据已保存: {file_path}")
        return file_path

if __name__ == "__main__":
    cleaner = DataCleaner()
    df = cleaner.clean()
    
    if df is not None:
        print(df.head())
        print(f"清洗后数据量: {len(df)}")
        cleaner.save_cleaned_data(df)
