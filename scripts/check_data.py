import pandas as pd
import os

file_path = r'c:\Users\31851\Desktop\抓取二手房数据\data\output\house_data.csv'

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    print(f'数据量: {len(df)}')
    print(f'列名: {df.columns.tolist()}')
    print(f'区县数量: {df["district"].nunique()}')
    print(f'平均单价: {df["unit_price"].mean():.0f} 元/平米')
    print(f'平均总价: {df["total_price"].mean():.0f} 万')
    print(f'数据来源: {df["source"].unique()}')
else:
    print('文件不存在')
