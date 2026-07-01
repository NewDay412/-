import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from storage.csv_storage import CSVStorage

def fix_unit_price():
    """修复单价数据：使用总价/面积计算单价"""
    storage = CSVStorage()
    df = storage.load_data()
    
    print(f"原始数据量: {len(df)}")
    
    if len(df) == 0:
        print("无数据可修复")
        return
    
    print(f"原始平均单价: {df['unit_price'].mean():.0f}")
    
    df['unit_price'] = df.apply(lambda row: round(row['total_price'] * 10000 / row['area'], 0) 
                                if row['area'] > 0 else 0, axis=1)
    
    print(f"修复后平均单价: {df['unit_price'].mean():.0f}")
    
    storage.save_data(df)
    print("单价修复完成")

if __name__ == "__main__":
    fix_unit_price()
