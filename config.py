import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB = os.getenv("MONGODB_DB", "chongqing_house")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "second_hand_houses")
    AMAP_KEY = os.getenv("AMAP_KEY", "")
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    CHONGQING_DISTRICTS = [
        "渝中区", "大渡口区", "江北区", "沙坪坝区", "九龙坡区",
        "南岸区", "北碚区", "渝北区", "巴南区", "万州区",
        "涪陵区", "黔江区", "长寿区", "江津区", "合川区",
        "永川区", "南川区", "綦江区", "大足区", "璧山区",
        "铜梁区", "潼南区", "荣昌区", "开州区", "梁平区",
        "武隆区"
    ]
    
    SPIDER_SETTINGS = {
        "MAX_WORKERS": 8,
        "REQUEST_DELAY": 2,
        "MAX_RETRIES": 3,
        "TIMEOUT": 30,
        "OUTPUT_DIR": "data/output",
        "LOG_DIR": "logs"
    }
