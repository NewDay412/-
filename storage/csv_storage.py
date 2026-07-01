import pandas as pd
import os
from loguru import logger
from config import Config
from datetime import datetime
from typing import List, Dict, Optional
from .base_storage import BaseStorage

class CSVStorage(BaseStorage):
    """CSV数据存储模块"""
    
    def __init__(self):
        self.data_dir = Config.SPIDER_SETTINGS["OUTPUT_DIR"]
        os.makedirs(self.data_dir, exist_ok=True)
        self.file_path = os.path.join(self.data_dir, "house_data.csv")
        self._df_cache = None
    
    def _load_to_cache(self):
        """加载数据到缓存"""
        if self._df_cache is None:
            if os.path.exists(self.file_path):
                self._df_cache = pd.read_csv(self.file_path)
                logger.debug(f"从CSV加载数据成功，共 {len(self._df_cache)} 条")
            else:
                self._df_cache = pd.DataFrame()
                logger.debug("CSV文件不存在，创建空DataFrame")
    
    def load_data(self) -> List[Dict]:
        """加载数据"""
        self._load_to_cache()
        return self._df_cache.to_dict('records')
    
    def save_data(self, data: List[Dict]) -> None:
        """保存数据"""
        df = pd.DataFrame(data)
        df.to_csv(self.file_path, index=False, encoding='utf-8-sig')
        self._df_cache = df
        logger.info(f"数据保存成功，共 {len(df)} 条")
    
    def insert_one(self, data: Dict) -> None:
        """插入单条数据"""
        self._load_to_cache()
        new_row = pd.DataFrame([data])
        self._df_cache = pd.concat([self._df_cache, new_row], ignore_index=True)
    
    def insert_many(self, data_list: List[Dict]) -> None:
        """批量插入数据"""
        self._load_to_cache()
        if data_list:
            new_data = pd.DataFrame(data_list)
            self._df_cache = pd.concat([self._df_cache, new_data], ignore_index=True)
            logger.debug(f"批量插入数据成功，数量: {len(data_list)}")
    
    def flush(self) -> None:
        """刷新缓存到磁盘"""
        if self._df_cache is not None and len(self._df_cache) > 0:
            self._df_cache.to_csv(self.file_path, index=False, encoding='utf-8-sig')
            logger.debug(f"缓存已刷新到磁盘，共 {len(self._df_cache)} 条")
    
    def count_documents(self) -> int:
        """统计文档数量"""
        self._load_to_cache()
        return len(self._df_cache)
    
    def find(self, query: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询数据"""
        self._load_to_cache()
        df = self._df_cache
        
        if query:
            for key, value in query.items():
                if key in df.columns:
                    df = df[df[key] == value]
        
        if limit:
            df = df.head(limit)
        
        return df.to_dict('records')
    
    def drop_collection(self) -> None:
        """删除数据"""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            self._df_cache = pd.DataFrame()
            logger.info("CSV数据已删除")
        else:
            logger.info("CSV文件不存在")
    
    def close(self) -> None:
        """关闭存储（刷新缓存）"""
        self.flush()
        logger.info("CSV存储已关闭")

if __name__ == "__main__":
    storage = CSVStorage()
    print(f"当前数据量: {storage.count_documents()}")