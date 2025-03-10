import os
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

def _get_env_var(key: str, default: Any = None, required: bool = True) -> Any:
    """
    获取环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
        required: 是否必需
        
    Returns:
        环境变量值
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"必需的环境变量 {key} 未设置")
    return value

def _parse_json_env(key: str, default: Any = None) -> Any:
    """
    解析JSON格式的环境变量
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        解析后的值
    """
    value = _get_env_var(key, required=False)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return default

# API配置
BINANCE_API_KEY = _get_env_var('BINANCE_API_KEY')
BINANCE_API_SECRET = _get_env_var('BINANCE_API_SECRET')
OPENAI_API_KEY = _get_env_var('OPENAI_API_KEY')

# 数据库配置
MONGODB_URI = _get_env_var('MONGODB_URI', 'mongodb://localhost:27017/')
REDIS_URI = _get_env_var('REDIS_URI', 'redis://localhost:6379')

# 应用配置
APP_ENV = _get_env_var('APP_ENV', 'development')
LOG_LEVEL = _get_env_var('LOG_LEVEL', 'INFO')
MAX_POSITION_SIZE = float(_get_env_var('MAX_POSITION_SIZE', 1000))  # USDT
RISK_LIMIT_PERCENTAGE = float(_get_env_var('RISK_LIMIT_PERCENTAGE', 2))  # %
STOP_LOSS_PERCENTAGE = float(_get_env_var('STOP_LOSS_PERCENTAGE', 1))  # %

# 交易配置
TRADING_PAIRS: List[str] = eval(_get_env_var('TRADING_PAIRS', '["BTCUSDT", "ETHUSDT"]'))
TRADING_INTERVAL = _get_env_var('TRADING_INTERVAL', '1m')
MAX_TRADES_PER_DAY = int(_get_env_var('MAX_TRADES_PER_DAY', 10))

# 监控配置
PROMETHEUS_PORT = int(_get_env_var('PROMETHEUS_PORT', 9090))
GRAFANA_PORT = int(_get_env_var('GRAFANA_PORT', 3000))

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
            'filename': _get_env_var('LOG_FILE', 'logs/trading.log'),
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
    # OpenAI配置
    'openai': {
        'api_key': _get_env_var('OPENAI_API_KEY'),
        'model': _get_env_var('OPENAI_MODEL', 'gpt-4-turbo-preview'),
        'temperature': float(_get_env_var('OPENAI_TEMPERATURE', '0.7')),
        'max_tokens': int(_get_env_var('OPENAI_MAX_TOKENS', '2000')),
        'base_url': _get_env_var('OPENAI_BASE_URL', 'https://api.deepseek.com', required=True),
        'org_id': _get_env_var('OPENAI_ORG_ID', required=False),
        'request_timeout': int(_get_env_var('OPENAI_REQUEST_TIMEOUT', '30')),
        'max_retries': int(_get_env_var('OPENAI_MAX_RETRIES', '3')),
        'retry_interval': int(_get_env_var('OPENAI_RETRY_INTERVAL', '1'))
    },
    
    # Anthropic配置（备选模型）
    'anthropic': {
        'api_key': _get_env_var('ANTHROPIC_API_KEY', required=False),
        'model': _get_env_var('ANTHROPIC_MODEL', 'claude-3-opus', required=False)
    },
    
    # Google AI配置（备选模型）
    'google': {
        'api_key': _get_env_var('GOOGLE_AI_API_KEY', required=False),
        'model': _get_env_var('GOOGLE_AI_MODEL', 'gemini-pro', required=False)
    },
    
    # 代理配置
    'proxy': {
        'url': _get_env_var('LLM_PROXY_URL', required=False),
        'key': _get_env_var('LLM_PROXY_KEY', required=False)
    }
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
    'rsi_period': int(_get_env_var('RSI_PERIOD', '14')),
    'ma_periods': [7, 25, 99],
    'bollinger_period': int(_get_env_var('BOLLINGER_PERIOD', '20')),
    'bollinger_std': float(_get_env_var('BOLLINGER_STD', '2')),
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
        'smtp_server': _get_env_var('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(_get_env_var('SMTP_PORT', 587)),
        'sender_email': _get_env_var('SENDER_EMAIL'),
        'sender_password': _get_env_var('SENDER_PASSWORD'),
    }
}

# 验证配置
def validate_config():
    """
    验证配置是否完整
    """
    required_configs = [
        ("OpenAI API密钥", MODEL_CONFIG['openai']['api_key']),
        ("数据库用户名", _get_env_var('DB_USER')),
        ("数据库密码", _get_env_var('DB_PASSWORD')),
        ("Binance API密钥", BINANCE_API_KEY),
        ("Binance API密钥", BINANCE_API_SECRET)
    ]
    
    # 验证备选模型配置的完整性
    if MODEL_CONFIG['anthropic']['api_key']:
        required_configs.append(("Anthropic模型名称", MODEL_CONFIG['anthropic']['model']))
    
    if MODEL_CONFIG['google']['api_key']:
        required_configs.append(("Google AI模型名称", MODEL_CONFIG['google']['model']))
    
    # 验证代理配置的完整性
    if MODEL_CONFIG['proxy']['url']:
        required_configs.append(("大模型代理密钥", MODEL_CONFIG['proxy']['key']))
    
    missing_configs = []
    for name, value in required_configs:
        if not value:
            missing_configs.append(name)
            
    if missing_configs:
        raise ValueError(f"缺少必需的配置项: {', '.join(missing_configs)}")
        
# 初始化时验证配置
validate_config() 