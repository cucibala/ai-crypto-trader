import os
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# API配置
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 数据库配置
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
REDIS_URI = os.getenv('REDIS_URI', 'redis://localhost:6379')

# 应用配置
APP_ENV = os.getenv('APP_ENV', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', 1000))  # USDT
RISK_LIMIT_PERCENTAGE = float(os.getenv('RISK_LIMIT_PERCENTAGE', 2))  # %
STOP_LOSS_PERCENTAGE = float(os.getenv('STOP_LOSS_PERCENTAGE', 1))  # %

# 交易配置
TRADING_PAIRS: List[str] = eval(os.getenv('TRADING_PAIRS', '["BTCUSDT", "ETHUSDT"]'))
TRADING_INTERVAL = os.getenv('TRADING_INTERVAL', '1m')
MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', 10))

# 监控配置
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 9090))
GRAFANA_PORT = int(os.getenv('GRAFANA_PORT', 3000))

# 日志配置
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': LOG_LEVEL,
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'standard',
            'level': LOG_LEVEL,
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True
        }
    }
}

# AI模型配置
MODEL_CONFIG = {
    'model': 'gpt-4',
    'temperature': 0.7,
    'max_tokens': 1000,
}

# 风险管理配置
RISK_MANAGEMENT = {
    'max_position_size': MAX_POSITION_SIZE,
    'risk_limit_percentage': RISK_LIMIT_PERCENTAGE,
    'stop_loss_percentage': STOP_LOSS_PERCENTAGE,
    'max_trades_per_day': MAX_TRADES_PER_DAY,
}

# 技术分析配置
TECHNICAL_ANALYSIS = {
    'rsi_period': 14,
    'ma_periods': [7, 25, 99],
    'bollinger_period': 20,
    'bollinger_std': 2,
}

# 数据采集配置
DATA_COLLECTION = {
    'kline_intervals': ['1m', '5m', '15m', '1h', '4h', '1d'],
    'order_book_depth': 100,
    'update_interval': 1,  # 秒
}

# 缓存配置
CACHE_CONFIG = {
    'ttl': 300,  # 5分钟
    'max_size': 1000,
}

# 通知配置
NOTIFICATION = {
    'enabled': True,
    'channels': ['log', 'email'],
    'email': {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_password': os.getenv('SENDER_PASSWORD'),
    }
} 