from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseStorage(ABC):
    """存储模块抽象基类"""
    
    @abstractmethod
    def load_data(self) -> List[Dict]:
        """加载数据"""
        pass
    
    @abstractmethod
    def save_data(self, data: List[Dict]) -> None:
        """保存数据"""
        pass
    
    @abstractmethod
    def insert_one(self, data: Dict) -> None:
        """插入单条数据"""
        pass
    
    @abstractmethod
    def insert_many(self, data_list: List[Dict]) -> None:
        """批量插入数据"""
        pass
    
    @abstractmethod
    def count_documents(self) -> int:
        """统计文档数量"""
        pass
    
    @abstractmethod
    def find(self, query: Optional[Dict] = None, limit: Optional[int] = None) -> List[Dict]:
        """查询数据"""
        pass
    
    @abstractmethod
    def drop_collection(self) -> None:
        """删除数据"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass