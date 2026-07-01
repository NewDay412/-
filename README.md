# 重庆市二手房价格数据分析与可视化系统

## 项目概述

本项目是一个基于 Python 的二手房数据爬取、分析与可视化系统，主要针对重庆市各区县的二手房市场数据进行采集、清洗、分析和展示。

### 功能特性

- ✅ **数据爬取**：支持安居客、链家两大平台的数据采集
- ✅ **数据清洗**：自动去重、缺失值处理、数据验证
- ✅ **数据存储**：CSV 文件存储 + MongoDB 存储
- ✅ **增量更新**：支持定期增量更新数据
- ✅ **数据挖掘**：K-Means 聚类分析、线性回归分析
- ✅ **可视化展示**：Web 端图表展示（ECharts）

## 环境要求

- Python 3.13+
- Chrome 浏览器（用于 Selenium）
- MongoDB（可选，用于数据存储）

## 快速开始

### 1. 安装依赖

```bash
cd 抓取二手房数据
pip install -r requirements.txt
```

### 2. 爬取数据

```bash
# 爬取安居客数据（需要浏览器验证）
python spiders/auto_spider.py

# 爬取链家数据（需要登录）
python spiders/lianjia_spider_fixed.py
```

### 3. 启动 Web 服务

```bash
python web/app.py
```

访问：http://127.0.0.1:5000

### 4. 使用主入口

```bash
# 爬取数据
python main.py crawl

# 清洗数据
python main.py clean

# 分析数据
python main.py analyze

# 启动 Web 服务
python main.py web

# 增量更新
python main.py update

# 执行全部流程
python main.py all
```

## 项目结构

```
抓取二手房数据/
├── main.py              # 主入口
├── config.py            # 配置文件
├── requirements.txt     # 依赖列表
├── .env                 # 环境变量
├── spiders/             # 爬虫模块
│   ├── auto_spider.py           # 全自动爬虫（安居客）
│   ├── lianjia_spider_fixed.py  # 链家爬虫（支持登录）
│   ├── cookie_based_spider.py   # Cookie 模式爬虫
│   └── ...
├── data_cleaning/       # 数据清洗
│   └── cleaner.py       # 清洗逻辑
├── data_mining/         # 数据挖掘
│   └── analyzer.py      # 分析算法
├── storage/             # 数据存储
│   ├── csv_storage.py   # CSV 存储
│   └── mongodb.py       # MongoDB 存储
├── incremental_update/  # 增量更新
│   └── updater.py       # 定时更新
├── web/                 # Web 可视化
│   ├── app.py           # Flask 后端
│   └── templates/       # HTML 模板
└── data/output/         # 数据输出
    └── house_data.csv   # 爬取的数据
```

## 数据字段说明

| 字段 | 说明 |
|------|------|
| title | 房源标题 |
| district | 区县 |
| location | 位置/小区名称 |
| total_price | 总价（万元） |
| unit_price | 单价（元/㎡） |
| area | 面积（㎡） |
| tags | 标签（精装修、近地铁等） |
| detail_url | 详情链接 |
| source | 数据来源（安居客/链家） |
| crawl_time | 爬取时间 |

## 可视化功能

1. **数据概览**：数据总量、平均价格等统计信息
2. **区县房价对比**：各区县平均单价柱状图
3. **价格区间分布**：房源价格分布直方图
4. **聚类分析**：基于价格和面积的 K-Means 聚类
5. **回归分析**：面积、单价与总价的关系

## 注意事项

1. **反爬机制**：安居客和链家都有严格的反爬机制，建议：
   - 使用浏览器模式爬虫
   - 适当增加请求间隔
   - 完成人机验证
   - 登录账号后爬取链家数据

2. **数据合规**：请遵守网站的 robots.txt 规则和使用条款

3. **数据量**：目标数据量为 5 万条以上，目前已爬取约 6.5 万条

## 技术栈

- **后端**：Python 3.13+、Flask
- **爬虫**：Selenium、BeautifulSoup、requests
- **数据处理**：pandas、numpy
- **数据挖掘**：scikit-learn（K-Means、线性回归）
- **可视化**：ECharts
- **存储**：CSV、MongoDB

## 许可证

本项目仅供学习和研究使用。
