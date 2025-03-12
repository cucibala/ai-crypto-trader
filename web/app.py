from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
from pathlib import Path
import logging
import numpy as np
from typing import List, Union

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from models.gpt_model import GPTModel
from models.base_model import BaseModel
from config.settings import MODEL_CONFIG
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 将格式化器添加到处理器
console_handler.setFormatter(formatter)

# 将处理器添加到日志记录器
if not logger.handlers:
    logger.addHandler(console_handler)
    
app = Flask(__name__)
CORS(app)

# 初始化币安客户端
from binance.client import Client
binance_client = Client(
    api_key=os.getenv('BINANCE_API_KEY'),
    api_secret=os.getenv('BINANCE_API_SECRET')
)

# 初始化 GPT 模型
gpt_model = GPTModel(api_key=os.getenv('OPENAI_API_KEY'))

def calculate_rsi(klines: List[List[Union[str, float]]], period: int = 14) -> Union[float, str]:
    """
    计算RSI指标
    """
    try:
        # 提取收盘价
        closes = np.array([float(k[4]) for k in klines])
        
        # 计算价格变化
        deltas = np.diff(closes)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down if down != 0 else 0
        rsi = np.zeros_like(closes)
        rsi[period] = 100. - 100./(1.+rs)

        # 计算RSI
        for i in range(period+1, len(closes)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(period-1) + upval)/period
            down = (down*(period-1) + downval)/period
            rs = up/down if down != 0 else 0
            rsi[i] = 100. - 100./(1.+rs)

        current_rsi = rsi[-1]
        logger.debug(f"计算得到的 RSI 值: {current_rsi:.2f}")
        return round(current_rsi, 2)
    except Exception as e:
        logger.error(f"RSI 计算失败: {str(e)}")
        return 'N/A'

def calculate_macd(klines: List[List[Union[str, float]]], fast: int = 12, slow: int = 26, signal: int = 9) -> Union[dict, str]:
    """
    计算MACD指标
    """
    try:
        # 提取收盘价
        closes = np.array([float(k[4]) for k in klines])
        
        # 计算EMA
        def ema(data, period):
            multiplier = 2 / (period + 1)
            ema = np.zeros_like(data)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
            return ema

        # 计算快线和慢线
        fast_ema = ema(closes, fast)
        slow_ema = ema(closes, slow)
        
        # 计算MACD线
        macd_line = fast_ema - slow_ema
        
        # 计算信号线
        signal_line = ema(macd_line, signal)
        
        # 计算MACD柱状图
        histogram = macd_line - signal_line
        
        result = {
            'macd': round(macd_line[-1], 2),
            'signal': round(signal_line[-1], 2),
            'histogram': round(histogram[-1], 2)
        }
        
        logger.debug(f"计算得到的 MACD 值: {result}")
        return result
    except Exception as e:
        logger.error(f"MACD 计算失败: {str(e)}")
        return 'N/A'

def calculate_bollinger_position(klines: List[List[Union[str, float]]], period: int = 20, num_std: float = 2.0) -> Union[str, float]:
    """
    计算布林带位置
    """
    try:
        # 提取收盘价
        closes = np.array([float(k[4]) for k in klines])
        
        if len(closes) < period:
            return 'N/A'
            
        # 计算移动平均线
        sma = np.mean(closes[-period:])
        
        # 计算标准差
        std = np.std(closes[-period:])
        
        # 计算布林带
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        # 计算当前价格在布林带中的位置 (0-100)
        current_price = closes[-1]
        band_width = upper_band - lower_band
        if band_width == 0:
            position = 50  # 如果带宽为0，则返回中间值
        else:
            position = ((current_price - lower_band) / band_width) * 100
            
        position = max(0, min(100, position))  # 确保值在0-100之间
        
        logger.debug(f"布林带位置: {position:.2f}%, 上轨: {upper_band:.2f}, 下轨: {lower_band:.2f}, 当前价格: {current_price:.2f}")
        return round(position, 2)
    except Exception as e:
        logger.error(f"布林带位置计算失败: {str(e)}")
        return 'N/A'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/balance', methods=['GET'])
def get_balance():
    try:
        # 获取账户信息
        account_info = binance_client.get_account()
        
        # 查找 BTC 和 USDT 余额
        btc_balance = 0
        usdt_balance = 0
        
        for balance in account_info['balances']:
            if balance['asset'] == 'BTC':
                btc_balance = float(balance['free']) + float(balance['locked'])
            elif balance['asset'] == 'USDT':
                usdt_balance = float(balance['free']) + float(balance['locked'])
        
        return jsonify({
            'success': True,
            'data': {
                'btc_balance': btc_balance,
                'usdt_balance': usdt_balance
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market_analysis', methods=['GET'])
def get_market_analysis():
    try:
        # 获取市场数据
        ticker = binance_client.get_symbol_ticker(symbol="BTCUSDT")
        
        # 获取足够的K线数据用于计算技术指标
        # 获取30天的数据，确保有足够数据计算所有指标
        klines = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1DAY, 
            limit=30
        )
        logger.debug(f"获取到 {len(klines)} 根K线数据")
        
        if len(klines) < 26:  # MACD需要26天数据
            logger.warning(f"K线数据不足，当前只有 {len(klines)} 根K线")
            
        depth = binance_client.get_order_book(symbol='BTCUSDT')
        
        # 获取24小时统计数据
        ticker_24h = binance_client.get_ticker(symbol='BTCUSDT')
        
        # 计算技术指标
        rsi_value = calculate_rsi(klines)
        macd_value = calculate_macd(klines)
        bollinger_value = calculate_bollinger_position(klines)
        
        logger.info(f"技术指标计算结果 - RSI: {rsi_value}, MACD: {macd_value}, 布林带位置: {bollinger_value}")
        
        market_data = {
            'symbol': 'BTCUSDT',
            'price': float(ticker['price']),
            'price_change_24h': float(ticker_24h['priceChangePercent']),
            'volume_24h': float(ticker_24h['volume']),  # 24小时成交量
            'quote_volume': float(ticker_24h['quoteVolume']),  # 24小时成交额(USDT)
            'base_volume': float(ticker_24h['volume']),  # 基础货币成交量(BTC)
            'volume_change_24h': 0,  # 需要历史数据才能计算
            'buy_volume': sum(float(bid[1]) for bid in depth['bids'][:10]),
            'sell_volume': sum(float(ask[1]) for ask in depth['asks'][:10]),
            'buy_depth': depth['bids'][:5],
            'sell_depth': depth['asks'][:5],
            'rsi': rsi_value,
            'macd': macd_value,
            'bollinger_position': bollinger_value
        }
        
        # 使用 GPT 模型分析市场
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analysis_result = loop.run_until_complete(gpt_model.analyze_market(market_data))
        
        # 生成交易策略
        strategy = loop.run_until_complete(gpt_model.generate_strategy(analysis_result))
        loop.close()
        
        return jsonify({
            'success': True,
            'data': {
                'market_data': market_data,
                'analysis': analysis_result,
                'strategy': strategy
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = request.json
    # TODO: 实现实际的交易逻辑
    return jsonify({
        'success': True,
        'message': '交易提交成功',
        'order_id': '123456789'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000) 