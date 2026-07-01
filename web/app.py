import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from loguru import logger
from storage.csv_storage import CSVStorage
from data_mining.analyzer import DataAnalyzer

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """返回favicon"""
    return '', 204

@app.route('/api/data/overview')
def get_overview():
    """获取数据概览"""
    try:
        storage = CSVStorage()
        count = storage.count_documents()
        
        return jsonify({
            'status': 'success',
            'total_count': count,
            'update_time': '2026-07-01'
        })
    except Exception as e:
        logger.error(f"获取数据概览失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/district')
def get_district_data():
    """获取区县数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.district_analysis()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取区县数据失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/price_range')
def get_price_range():
    """获取价格区间数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.price_range_analysis()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取价格区间数据失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/basic_stats')
def get_basic_stats():
    """获取基础统计数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.basic_statistics()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取基础统计数据失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/clustering')
def get_clustering():
    """获取聚类分析数据"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.clustering_analysis()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取聚类分析数据失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/conclusions')
def get_conclusions():
    """获取分析结论"""
    try:
        analyzer = DataAnalyzer()
        analyzer.use_csv = True
        result = analyzer.generate_conclusions()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        logger.error(f"获取分析结论失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data/raw')
def get_raw_data():
    """获取原始数据（分页）"""
    try:
        storage = CSVStorage()
        data = storage.find(limit=100)
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"获取原始数据失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"启动Flask服务器，地址: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)
