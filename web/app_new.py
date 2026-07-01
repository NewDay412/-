import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify
from storage.csv_storage import CSVStorage
import pandas as pd
import numpy as np
from data_mining.analyzer import DataAnalyzer

app = Flask(__name__)
storage = CSVStorage()
analyzer = DataAnalyzer()

@app.route('/')
def index():
    return render_template('index_new.html')

@app.route('/api/house_count')
def house_count():
    df = storage.load_data()
    return jsonify({'count': len(df)})

@app.route('/api/district_stats')
def district_stats():
    df = storage.load_data()
    
    district_stats = df.groupby('district').agg(
        count=('title', 'count'),
        avg_total_price=('total_price', 'mean'),
        avg_unit_price=('unit_price', 'mean'),
        avg_area=('area', 'mean')
    ).reset_index()
    
    district_stats['avg_total_price'] = district_stats['avg_total_price'].round(1)
    district_stats['avg_unit_price'] = district_stats['avg_unit_price'].round(0)
    district_stats['avg_area'] = district_stats['avg_area'].round(1)
    
    return jsonify(district_stats.to_dict('records'))

@app.route('/api/price_distribution')
def price_distribution():
    df = storage.load_data()
    
    bins = [0, 50, 80, 100, 150, 200, 300, 500, 1000]
    labels = ['50万以下', '50-80万', '80-100万', '100-150万', '150-200万', '200-300万', '300-500万', '500万以上']
    df['price_range'] = pd.cut(df['total_price'], bins=bins, labels=labels)
    
    distribution = df['price_range'].value_counts().sort_index().to_dict()
    
    return jsonify({
        'labels': list(distribution.keys()),
        'values': list(distribution.values())
    })

@app.route('/api/area_distribution')
def area_distribution():
    df = storage.load_data()
    
    bins = [0, 50, 70, 90, 110, 130, 150, 200, 500]
    labels = ['50㎡以下', '50-70㎡', '70-90㎡', '90-110㎡', '110-130㎡', '130-150㎡', '150-200㎡', '200㎡以上']
    df['area_range'] = pd.cut(df['area'], bins=bins, labels=labels)
    
    distribution = df['area_range'].value_counts().sort_index().to_dict()
    
    return jsonify({
        'labels': list(distribution.keys()),
        'values': list(distribution.values())
    })

@app.route('/api/source_distribution')
def source_distribution():
    df = storage.load_data()
    distribution = df['source'].value_counts().to_dict()
    return jsonify(distribution)

@app.route('/api/cluster_data')
def cluster_data():
    df = storage.load_data()
    if len(df) < 100:
        return jsonify([])
    
    cluster_result = analyzer.cluster_analysis(df)
    
    return jsonify(cluster_result)

@app.route('/api/top_houses')
def top_houses():
    df = storage.load_data()
    top_houses = df.nlargest(10, 'total_price')[['title', 'district', 'total_price', 'unit_price', 'area']].to_dict('records')
    return jsonify(top_houses)

@app.route('/api/overview')
def overview():
    df = storage.load_data()
    
    stats = {
        'total_count': len(df),
        'avg_total_price': round(df['total_price'].mean(), 1) if len(df) > 0 else 0,
        'avg_unit_price': round(df['unit_price'].mean(), 0) if len(df) > 0 else 0,
        'avg_area': round(df['area'].mean(), 1) if len(df) > 0 else 0,
        'max_price': round(df['total_price'].max(), 1) if len(df) > 0 else 0,
        'min_price': round(df['total_price'].min(), 1) if len(df) > 0 else 0,
        'district_count': df['district'].nunique(),
        'source_count': df['source'].nunique()
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
