import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import json

class DataAnalyzer:
    """数据挖掘与分析模块"""
    
    def __init__(self):
        self.use_csv = False
        self.df = None
    
    def load_data(self):
        """加载数据"""
        logger.info("开始加载数据")
        
        if self.use_csv:
            from storage.csv_storage import CSVStorage
            storage = CSVStorage()
            self.df = storage.load_data()
        else:
            from storage.mongodb import MongoDBStorage
            storage = MongoDBStorage()
            data = storage.find({}, {'_id': 0})
            self.df = pd.DataFrame(data)
            storage.close()
        
        logger.info(f"加载数据完成，共 {len(self.df)} 条")
        return self.df
    
    def basic_statistics(self):
        """基础统计分析"""
        if self.df is None:
            self.load_data()
        
        logger.info("开始基础统计分析")
        
        statistics = {
            'total_count': len(self.df),
            'avg_total_price': round(self.df['total_price'].mean(), 2),
            'median_total_price': round(self.df['total_price'].median(), 2),
            'min_total_price': round(self.df['total_price'].min(), 2),
            'max_total_price': round(self.df['total_price'].max(), 2),
            'avg_unit_price': round(self.df['unit_price'].mean(), 2),
            'median_unit_price': round(self.df['unit_price'].median(), 2),
            'avg_area': round(self.df['area'].mean(), 2),
            'district_count': self.df['district'].nunique()
        }
        
        logger.info(f"基础统计完成:\n{statistics}")
        return statistics
    
    def district_analysis(self):
        """各区县房价分析"""
        if self.df is None:
            self.load_data()
        
        logger.info("开始各区县房价分析")
        
        district_stats = self.df.groupby('district').agg({
            'total_price': ['mean', 'median', 'count'],
            'unit_price': ['mean', 'median'],
            'area': ['mean']
        }).round(2)
        
        district_stats.columns = ['平均总价', '中位数总价', '房源数量', '平均单价', '中位数单价', '平均面积']
        district_stats = district_stats.sort_values('平均单价', ascending=False)
        
        result = district_stats.reset_index().to_dict('records')
        logger.info("区县分析完成")
        return result
    
    def price_range_analysis(self):
        """价格区间分析"""
        if self.df is None:
            self.load_data()
        
        logger.info("开始价格区间分析")
        
        bins = [0, 50, 100, 150, 200, 300, 500, np.inf]
        labels = ['50万以下', '50-100万', '100-150万', '150-200万', '200-300万', '300-500万', '500万以上']
        
        self.df['price_range'] = pd.cut(self.df['total_price'], bins=bins, labels=labels)
        
        price_distribution = self.df['price_range'].value_counts().sort_index().to_dict()
        
        logger.info(f"价格区间分析完成:\n{price_distribution}")
        return price_distribution
    
    def clustering_analysis(self, n_clusters=5):
        """聚类分析"""
        if self.df is None:
            self.load_data()
        
        logger.info("开始聚类分析")
        
        features = self.df[['unit_price', 'area', 'total_price']].dropna()
        
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(scaled_features)
        
        cluster_stats = []
        for i in range(n_clusters):
            cluster_data = features[labels == i]
            cluster_stats.append({
                'cluster': i,
                'count': len(cluster_data),
                'avg_unit_price': round(cluster_data['unit_price'].mean(), 2),
                'avg_area': round(cluster_data['area'].mean(), 2),
                'avg_total_price': round(cluster_data['total_price'].mean(), 2)
            })
        
        logger.info("聚类分析完成")
        return cluster_stats
    
    def regression_analysis(self):
        """回归分析"""
        if self.df is None:
            self.load_data()
        
        logger.info("开始回归分析")
        
        X = self.df[['area', 'unit_price']].dropna()
        y = self.df.loc[X.index, 'total_price']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        mse = round(mean_squared_error(y_test, y_pred), 2)
        r2 = round(r2_score(y_test, y_pred), 4)
        
        analysis_result = {
            'coefficients': {
                'area': round(model.coef_[0], 4),
                'unit_price': round(model.coef_[1], 4)
            },
            'intercept': round(model.intercept_, 4),
            'mse': mse,
            'r2': r2,
            'feature_importance': {
                'area': abs(model.coef_[0]),
                'unit_price': abs(model.coef_[1])
            }
        }
        
        logger.info(f"回归分析完成:\n{analysis_result}")
        return analysis_result
    
    def generate_conclusions(self):
        """生成分析结论"""
        logger.info("开始生成分析结论")
        
        basic_stats = self.basic_statistics()
        district_stats = self.district_analysis()
        price_range = self.price_range_analysis()
        cluster_stats = self.clustering_analysis()
        regression_result = self.regression_analysis()
        
        conclusions = {
            'basic_statistics': basic_stats,
            'district_analysis': district_stats,
            'price_range_analysis': price_range,
            'clustering_analysis': cluster_stats,
            'regression_analysis': regression_result,
            'key_findings': [
                f"重庆市二手房平均总价约 {basic_stats['avg_total_price']} 万，平均单价约 {basic_stats['avg_unit_price']} 元/平米",
                f"房价最高的区域是 {district_stats[0]['district']}，平均单价 {district_stats[0]['平均单价']} 元/平米",
                f"房价最低的区域是 {district_stats[-1]['district']}，平均单价 {district_stats[-1]['平均单价']} 元/平米",
                f"大部分房源价格集中在 {max(price_range, key=price_range.get)} 区间",
                f"回归模型R²为 {regression_result['r2']}，面积和单价是影响总价的主要因素"
            ]
        }
        
        logger.info("分析结论生成完成")
        return conclusions

if __name__ == "__main__":
    analyzer = DataAnalyzer()
    analyzer.use_csv = True
    conclusions = analyzer.generate_conclusions()
    
    print(json.dumps(conclusions, ensure_ascii=False, indent=2))
