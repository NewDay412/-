# 重庆市二手房价格数据分析与可视化系统 - 技术教学文档

## 第一章：项目架构设计

### 1.1 整体架构

本项目采用模块化设计，分为以下几个核心模块：

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (Web)                       │
│              Flask + ECharts + HTML/CSS/JS                  │
├─────────────────────────────────────────────────────────────┤
│                      业务逻辑层                              │
│          数据爬取 | 数据清洗 | 数据分析 | 增量更新            │
├─────────────────────────────────────────────────────────────┤
│                      数据存储层                              │
│                  CSV 文件 | MongoDB 数据库                   │
├─────────────────────────────────────────────────────────────┤
│                      外部数据源                              │
│                  安居客 | 链家 (API/HTML)                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责划分

| 模块 | 职责 | 核心技术 |
|------|------|----------|
| spiders | 数据采集 | Selenium、requests、BeautifulSoup |
| data_cleaning | 数据清洗 | pandas、正则表达式 |
| data_mining | 数据分析 | scikit-learn（K-Means、线性回归） |
| storage | 数据存储 | CSV、MongoDB |
| web | 可视化展示 | Flask、ECharts |

---

## 第二章：爬虫技术实现

### 2.1 爬虫架构设计

```python
# 爬虫基类设计原则
class BaseSpider:
    def __init__(self):
        self.headers = self._build_headers()
        self.session = self._create_session()
        self.storage = CSVStorage()
    
    def _build_headers(self):
        """构建请求头，模拟浏览器"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
```

### 2.2 Selenium 反爬绕过技术

#### 2.2.1 隐藏 WebDriver 特征

```python
# 关键配置：隐藏自动化特征
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# CDP 命令注入，彻底隐藏 webdriver 属性
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
    '''
})
```

#### 2.2.2 模拟人类行为

```python
def simulate_human(self):
    """模拟人类行为，降低被识别风险"""
    # 随机滚动
    for _ in range(random.randint(2, 4)):
        scroll_amount = random.uniform(100, 300)
        self.driver.execute_script(f'window.scrollBy(0, {scroll_amount})')
        self.random_delay(0.3, 0.8)
    
    # 随机鼠标移动
    action = ActionChains(self.driver)
    for _ in range(random.randint(2, 3)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        action.move_by_offset(x, y).pause(random.uniform(0.1, 0.3))
    action.perform()
```

### 2.3 反爬检测与处理

```python
def is_blocked(self):
    """检测是否被反爬拦截"""
    page_source = self.driver.page_source.lower()
    
    # 网易易盾验证码检测
    if 'yidun' in page_source or 'captcha-wy' in page_source:
        return True
    
    # 通用验证码检测
    if '请验证您是真人' in page_source or '人机验证' in page_source:
        return True
    
    # 反垃圾检测
    if 'antispam' in page_source or 'captcha' in page_source:
        return True
    
    return False
```

### 2.4 数据解析技术

```python
def parse_anjuke(self, html, district):
    """解析安居客页面数据"""
    soup = BeautifulSoup(html, 'lxml')
    
    # 多重选择器策略，应对页面结构变化
    items = soup.select('.property-ex') or soup.select('.list-item') or soup.select('[class*="property"]')
    
    for item in items:
        # 价格解析（核心逻辑）
        price_total_text = item.select_one('.property-price-total').get_text(strip=True)
        price_avg_text = item.select_one('.property-price-average').get_text(strip=True)
        
        # 正则提取数字
        total_price = float(re.search(r'(\d+(?:\.\d+)?)', price_total_text).group(1))
        
        # 单价解析（从元转换为元/㎡）
        unit_price_val = float(re.search(r'(\d+)', price_avg_text).group(1))
        
        # 面积解析
        area_match = re.search(r'(\d+(?:\.\d+)?)㎡', info_text)
        area = float(area_match.group(1)) if area_match else 0
        
        # 备用计算：通过总价和面积反推单价
        if unit_price_val == 0 and total_price > 0 and area > 0:
            unit_price_val = round(total_price * 10000 / area, 0)
```

---

## 第三章：数据清洗技术

### 3.1 数据清洗流程

```
原始数据 → 缺失值处理 → 去重 → 异常值检测 → 格式转换 → 特征提取 → 清洗后数据
```

### 3.2 核心清洗逻辑

```python
class DataCleaner:
    def clean(self):
        """数据清洗主流程"""
        # 1. 加载原始数据
        df = self.load_raw_data()
        
        # 2. 去重
        df = df.drop_duplicates(subset=['title', 'district', 'total_price', 'area'])
        
        # 3. 缺失值处理
        df = df.dropna(subset=['title', 'total_price', 'area'])
        df['unit_price'] = df['unit_price'].fillna(0)
        
        # 4. 异常值过滤
        df = df[(df['total_price'] > 0) & (df['total_price'] < 10000)]
        df = df[(df['area'] > 20) & (df['area'] < 500)]
        
        # 5. 计算缺失的单价
        mask = (df['unit_price'] == 0) & (df['total_price'] > 0) & (df['area'] > 0)
        df.loc[mask, 'unit_price'] = round(df.loc[mask, 'total_price'] * 10000 / df.loc[mask, 'area'], 0)
        
        return df
```

---

## 第四章：数据挖掘算法

### 4.1 K-Means 聚类分析

#### 4.1.1 算法原理

K-Means 是一种无监督学习算法，用于将数据划分为 K 个簇。算法步骤：

1. 随机选择 K 个初始质心
2. 计算每个样本到质心的距离，分配到最近的簇
3. 更新每个簇的质心（取平均值）
4. 重复步骤 2-3，直到质心稳定

#### 4.1.2 代码实现

```python
def clustering_analysis(self, n_clusters=5):
    """K-Means 聚类分析"""
    # 特征选择与标准化
    features = self.df[['unit_price', 'area', 'total_price']].dropna()
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # K-Means 聚类
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(scaled_features)
    
    # 统计每个簇的特征
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
    
    return cluster_stats
```

### 4.2 线性回归分析

#### 4.2.1 算法原理

线性回归用于建立自变量与因变量之间的线性关系：
```
y = β₀ + β₁x₁ + β₂x₂ + ... + βₙxₙ
```

评估指标：
- **MSE（均方误差）**：衡量预测值与真实值的平均偏差
- **R²（决定系数）**：衡量模型解释方差的能力（0-1）

#### 4.2.2 代码实现

```python
def regression_analysis(self):
    """线性回归分析"""
    # 特征与目标变量
    X = self.df[['area', 'unit_price']].dropna()
    y = self.df.loc[X.index, 'total_price']
    
    # 数据分割
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 训练模型
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # 预测与评估
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    return {
        'coefficients': {
            'area': model.coef_[0],
            'unit_price': model.coef_[1]
        },
        'r2': r2,
        'mse': mse
    }
```

---

## 第五章：数据可视化技术

### 5.1 后端 API 设计

```python
@app.route('/api/data/district')
def get_district_data():
    """获取区县房价数据"""
    analyzer = DataAnalyzer()
    analyzer.use_csv = True
    result = analyzer.district_analysis()
    return jsonify({'status': 'success', 'data': result})

@app.route('/api/data/clustering')
def get_clustering():
    """获取聚类分析数据"""
    analyzer = DataAnalyzer()
    analyzer.use_csv = True
    result = analyzer.clustering_analysis()
    return jsonify({'status': 'success', 'data': result})
```

### 5.2 前端 ECharts 集成

```javascript
// 区县房价对比柱状图
function initDistrictChart() {
    fetch('/api/data/district')
        .then(res => res.json())
        .then(data => {
            const districts = data.data.map(item => item.district);
            const prices = data.data.map(item => item.平均单价);
            
            const chart = echarts.init(document.getElementById('districtChart'));
            chart.setOption({
                title: { text: '各区县二手房平均单价' },
                xAxis: { type: 'category', data: districts },
                yAxis: { type: 'value', name: '单价(元/㎡)' },
                series: [{
                    type: 'bar',
                    data: prices,
                    itemStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#83bff6' },
                            { offset: 0.5, color: '#188df0' },
                            { offset: 1, color: '#188df0' }
                        ])
                    }
                }]
            });
        });
}
```

---

## 第六章：增量更新机制

### 6.1 增量更新策略

```python
class IncrementalUpdater:
    def update(self):
        """增量更新主流程"""
        # 1. 获取上次更新时间
        last_update_time = self.get_last_update_time()
        
        # 2. 爬取新数据（只获取更新时间之后的）
        new_data = self.crawl_new_data(since=last_update_time)
        
        # 3. 去重（与已有数据对比）
        unique_data = self.remove_duplicates(new_data)
        
        # 4. 保存新数据
        self.save_new_data(unique_data)
        
        # 5. 更新时间戳
        self.update_last_update_time()
        
        return {'updated_count': len(unique_data)}
```

---

## 第七章：性能优化技巧

### 7.1 多线程爬取

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def crawl_district(self, district, url):
    """爬取单个区县数据"""
    data_list = []
    for page in range(1, 51):
        page_url = f"{url}p{page}/"
        html = self.fetch_page(page_url)
        data = self.parse_anjuke(html, district)
        data_list.extend(data)
    return data_list

def crawl_with_threads(self):
    """多线程爬取"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for district, url in self.district_urls.items():
            future = executor.submit(self.crawl_district, district, url)
            futures.append(future)
        
        for future in as_completed(futures):
            data_list = future.result()
            self.storage.insert_many(data_list)
```

### 7.2 请求缓存与重试

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_page(self, url):
    """带重试机制的页面请求"""
    response = self.session.get(url, headers=self.headers, timeout=30)
    response.raise_for_status()
    return response.text
```

---

## 第八章：常见问题与解决方案

### 8.1 反爬拦截问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 验证码页面 | 频繁请求被识别 | 使用浏览器模式，人工验证 |
| IP 封禁 | 单 IP 请求过多 | 使用代理 IP 池 |
| Cookie 失效 | 会话过期 | 定期更新 Cookie |

### 8.2 数据解析问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 价格为 0 | 选择器失效 | 多重选择器策略 |
| 页面结构变化 | 网站更新 | 动态选择器适配 |
| 中文乱码 | 编码不一致 | 指定 UTF-8 编码 |

### 8.3 性能问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 爬取速度慢 | 单线程串行 | 多线程/异步爬取 |
| 内存溢出 | 数据量大 | 分批处理、流式存储 |
| 存储慢 | 频繁 IO | 批量写入、缓存机制 |

---

## 第九章：扩展建议

### 9.1 增加更多数据源

- 贝壳网（Ke.com）
- 58 同城
- 房天下

### 9.2 增强反爬能力

- 代理 IP 池
- 浏览器指纹随机化
- 分布式爬取架构

### 9.3 深入数据分析

- 时间序列分析（房价趋势）
- 地理空间分析（热力图）
- 文本挖掘（房源描述分析）

### 9.4 部署优化

- Docker 容器化
- 云服务器部署
- 定时任务自动执行

---

## 附录：技术栈版本说明

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.13+ | 编程语言 |
| Flask | 2.2.5 | Web 框架 |
| Selenium | 4.18.1 | 浏览器自动化 |
| BeautifulSoup | 4.12.2 | HTML 解析 |
| pandas | 2.1.4 | 数据处理 |
| numpy | 1.26.3 | 数值计算 |
| scikit-learn | 1.3.2 | 机器学习 |
| ECharts | 5.4.3 | 数据可视化 |
| MongoDB | 6.0+ | 数据库存储 |

---

**文档版本**: v1.0  
**创建时间**: 2026-07-01  
**适用场景**: 学年设计、课程设计、毕业设计
