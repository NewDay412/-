from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from loguru import logger
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from storage.csv_storage import CSVStorage
from data_mining.analyzer import DataAnalyzer

app = Flask(__name__)
CORS(app)

def api_response(data=None, message=None, status='success', code=200):
    """统一API响应格式"""
    response = {'status': status}
    if data is not None:
        response['data'] = data
    if message is not None:
        response['message'] = message
    return jsonify(response), code

def api_error(message, code=500):
    """统一错误响应"""
    logger.error(f"API错误: {message}")
    return api_response(message=message, status='error', code=code)

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """返回favicon"""
    return '', 204

@app.route('/api')
def api_doc():
    """API文档"""
    docs = {
        'description': '重庆市二手房数据分析API',
        'endpoints': {
            '/api/data/overview': {
                'method': 'GET',
                'description': '获取数据概览',
                'response': {'status': 'success', 'total_count': 1000, 'update_time': '2026-07-01'}
            },
            '/api/data/district': {
                'method': 'GET',
                'description': '获取各区县房价分析数据',
                'response': {'status': 'success', 'data': [...]}
            },
            '/api/data/price_range': {
                'method': 'GET',
                'description': '获取价格区间分布',
                'response': {'status': 'success', 'data': {...}}
            },
            '/api/data/basic_stats': {
                'method': 'GET',
                'description': '获取基础统计数据',
                'response': {'status': 'success', 'data': {...}}
            },
            '/api/data/clustering': {
                'method': 'GET',
                'description': '获取聚类分析结果',
                'response': {'status': 'success', 'data': [...]}
            },
            '/api/data/conclusions': {
                'method': 'GET',
                'description': '获取完整分析结论',
                'response': {'status': 'success', 'data': {...}}
            },
            '/api/data/raw': {
                'method': 'GET',
                'description': '获取原始数据（默认100条）',
                'params': {'limit': '返回条数，默认100'},
                'response': {'status': 'success', 'data': [...]}
            }
        }
    }
    return api_response(data=docs)

@app.route('/api/data/overview')
def get_overview():
    """获取数据概览"""
    try:
        storage = CSVStorage()
        count = storage.count_documents()
        
        return api_response({
            'total_count': count,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return api_error(f"获取数据概览失败: {e}")

@app.route('/api/data/district')
def get_district_data():
    """获取区县数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.district_analysis()
        
        return api_response(data=result)
    except Exception as e:
        return api_error(f"获取区县数据失败: {e}")

@app.route('/api/data/price_range')
def get_price_range():
    """获取价格区间数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.price_range_analysis()
        
        return api_response(data=result)
    except Exception as e:
        return api_error(f"获取价格区间数据失败: {e}")

@app.route('/api/data/basic_stats')
def get_basic_stats():
    """获取基础统计数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.basic_statistics()
        
        return api_response(data=result)
    except Exception as e:
        return api_error(f"获取基础统计数据失败: {e}")

@app.route('/api/data/clustering')
def get_clustering():
    """获取聚类分析数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.clustering_analysis()
        
        return api_response(data=result)
    except Exception as e:
        return api_error(f"获取聚类分析数据失败: {e}")

@app.route('/api/data/conclusions')
def get_conclusions():
    """获取分析结论"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.generate_conclusions()
        
        return api_response(data=result)
    except Exception as e:
        return api_error(f"获取分析结论失败: {e}")

@app.route('/api/data/raw')
def get_raw_data():
    """获取原始数据（分页）"""
    try:
        limit = int(request.args.get('limit', 100))
        storage = CSVStorage()
        data = storage.find(limit=limit)
        
        return api_response(data=data)
    except ValueError:
        return api_error("参数limit必须为整数", 400)
    except Exception as e:
        return api_error(f"获取原始数据失败: {e}")

if __name__ == '__main__':
    logger.info(f"启动Flask服务器，地址: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)