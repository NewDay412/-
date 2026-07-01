import argparse
from loguru import logger
import os
from config import Config

def setup_logging():
    """配置日志"""
    log_dir = Config.SPIDER_SETTINGS["LOG_DIR"]
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(
        os.path.join(log_dir, "app.log"),
        rotation="1 day",
        retention="7 days",
        level="INFO",
        encoding="utf-8"
    )
    
    logger.info("日志配置完成")

def crawl_data():
    """爬取数据"""
    logger.info("开始爬取数据")
    
    try:
        from spiders.anjuke_spider import AnjukeSpider
        from spiders.lianjia_spider import LianjiaSpider
        
        anjuke_spider = AnjukeSpider()
        anjuke_spider.crawl()
        
        lianjia_spider = LianjiaSpider()
        lianjia_spider.crawl()
        
        logger.info("数据爬取完成")
        
    except Exception as e:
        logger.error(f"数据爬取失败: {e}")
        raise

def clean_data():
    """清洗数据"""
    logger.info("开始清洗数据")
    
    try:
        from data_cleaning.cleaner import DataCleaner
        
        cleaner = DataCleaner()
        df = cleaner.clean()
        
        if df is not None:
            cleaner.save_cleaned_data(df)
        
        cleaner.storage.close()
        logger.info("数据清洗完成")
        
    except Exception as e:
        logger.error(f"数据清洗失败: {e}")
        raise

def analyze_data():
    """分析数据"""
    logger.info("开始分析数据")
    
    try:
        from data_mining.analyzer import DataAnalyzer
        import json
        
        analyzer = DataAnalyzer()
        conclusions = analyzer.generate_conclusions()
        
        output_dir = Config.SPIDER_SETTINGS["OUTPUT_DIR"]
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, "analysis_results.json"), 'w', encoding='utf-8') as f:
            json.dump(conclusions, f, ensure_ascii=False, indent=2)
        
        logger.info("分析结果已保存")
        analyzer.storage.close()
        
        return conclusions
        
    except Exception as e:
        logger.error(f"数据分析失败: {e}")
        raise

def start_web_server():
    """启动Web服务器"""
    logger.info("启动Web服务器")
    
    try:
        from web.app import app
        
        app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)
        
    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        raise

def incremental_update():
    """增量更新"""
    logger.info("执行增量更新")
    
    try:
        from incremental_update.updater import IncrementalUpdater
        
        updater = IncrementalUpdater()
        result = updater.update()
        
        logger.info(f"增量更新结果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"增量更新失败: {e}")
        raise

def main():
    """主函数"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="重庆市二手房价格数据分析与可视化系统")
    parser.add_argument('action', choices=['crawl', 'clean', 'analyze', 'web', 'update', 'all'],
                        help='执行的操作: crawl(爬取), clean(清洗), analyze(分析), web(启动服务), update(增量更新), all(全部执行)')
    
    args = parser.parse_args()
    
    if args.action == 'crawl':
        crawl_data()
    elif args.action == 'clean':
        clean_data()
    elif args.action == 'analyze':
        analyze_data()
    elif args.action == 'web':
        start_web_server()
    elif args.action == 'update':
        incremental_update()
    elif args.action == 'all':
        crawl_data()
        clean_data()
        analyze_data()
        start_web_server()
    else:
        logger.error("无效的操作参数")

if __name__ == "__main__":
    main()
