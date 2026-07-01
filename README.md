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

- Python 3.13+（推荐 3.14）
- Chrome 浏览器（用于 Selenium）
- MongoDB（可选，用于数据存储）

## 快速开始

### 1. 安装依赖

```bash
cd 二手房数据抓取
pip install -r requirements.txt
```

### 2. 爬取数据

使用主入口 `main.py` 进行爬取（推荐）：

```bash
# 爬取数据（安居客 + 链家）
python main.py crawl

# 单独运行爬虫
python spiders/anjuke_spider.py
python spiders/lianjia_spider.py
```

### 3. 启动 Web 服务

```bash
python main.py web
```

访问：http://127.0.0.1:5000

### 4. 完整命令列表

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
二手房数据抓取/
├── main.py              # 主入口
├── config.py            # 配置文件
├── requirements.txt     # 依赖列表
├── .env                 # 环境变量
├── spiders/             # 爬虫模块
│   ├── __init__.py      # 模块导出
│   ├── base_spider.py   # 爬虫基类
│   ├── anjuke_spider.py # 安居客爬虫（增强版）
│   └── lianjia_spider.py # 链家爬虫
├── data_cleaning/       # 数据清洗
│   ├── __init__.py      # 模块导出
│   └── cleaner.py       # 清洗逻辑
├── data_mining/         # 数据挖掘
│   ├── __init__.py      # 模块导出
│   └── analyzer.py      # 分析算法
├── storage/             # 数据存储
│   ├── __init__.py      # 模块导出
│   ├── base_storage.py  # 存储抽象基类
│   ├── csv_storage.py   # CSV 存储
│   └── mongodb.py       # MongoDB 存储
├── incremental_update/  # 增量更新
│   ├── __init__.py      # 模块导出
│   └── updater.py       # 定时更新
├── scripts/             # 辅助脚本
│   ├── __init__.py      # 模块导出
│   ├── check_data.py    # 数据检查
│   └── fix_unit_price.py # 单价修复
├── web/                 # Web 可视化
│   ├── __init__.py      # 模块导出
│   ├── app.py           # Flask 后端
│   └── templates/       # HTML 模板
│       └── index.html   # 可视化页面
└── data/output/         # 数据输出
    └── house_data.csv   # 爬取的数据
```

## 依赖说明

### 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| requests | 2.31.0 | HTTP 请求 |
| beautifulsoup4 | 4.12.2 | HTML 解析 |
| lxml | 5.1.0 | XML/HTML 解析器 |
| selenium | 4.18.1 | 浏览器自动化 |
| fake-useragent | 1.4.0 | 随机 User-Agent |
| pandas | 2.1.4 | 数据处理 |
| numpy | 1.26.3 | 数值计算 |
| pymongo | 4.6.1 | MongoDB 驱动 |
| scikit-learn | 1.3.2 | 机器学习（聚类、回归） |
| flask | 2.2.5 | Web 框架 |
| flask-cors | 4.0.0 | 跨域支持 |
| python-dotenv | 1.0.0 | 环境变量加载 |
| loguru | 0.7.2 | 日志记录 |
| geopy | 2.4.1 | 地理编码（可选） |

### 安装步骤

```bash
# 确保 Python 版本正确
python --version

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 注意事项

1. **Chrome 浏览器**：需安装 Chrome 浏览器，并确保版本与 selenium 兼容
2. **ChromeDriver**：selenium 4.x 会自动下载 ChromeDriver，无需手动安装
3. **MongoDB**：如需使用 MongoDB 存储，需安装并启动 MongoDB 服务
4. **环境变量**：复制 `.env.example` 为 `.env`，配置相关参数

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
3. **价格区间分布**：房源价格分布折线图
4. **聚类分析**：基于价格和面积的 K-Means 聚类
5. **房价热力图**：各区域房价热力图
6. **分析结论**：自动生成的数据分析结论

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api` | GET | API 文档 |
| `/api/data/overview` | GET | 数据概览 |
| `/api/data/district` | GET | 区县房价分析 |
| `/api/data/price_range` | GET | 价格区间分布 |
| `/api/data/basic_stats` | GET | 基础统计数据 |
| `/api/data/clustering` | GET | 聚类分析 |
| `/api/data/conclusions` | GET | 分析结论 |
| `/api/data/raw` | GET | 原始数据 |

## 注意事项

1. **反爬机制**：安居客和链家都有严格的反爬机制，建议：
   - 使用浏览器模式爬虫
   - 适当增加请求间隔
   - 完成人机验证
   - 登录账号后爬取链家数据

2. **数据合规**：请遵守网站的 robots.txt 规则和使用条款

3. **数据量**：目标数据量为 5 万条以上

## 技术栈

- **后端**：Python 3.13+、Flask
- **爬虫**：Selenium、BeautifulSoup、requests
- **数据处理**：pandas、numpy
- **数据挖掘**：scikit-learn（K-Means、线性回归）
- **可视化**：ECharts
- **存储**：CSV、MongoDB

## 许可证

本项目仅供学习和研究使用。