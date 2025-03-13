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
from models.database import get_recent_strategies, get_recent_market_analysis, save_market_analysis, save_trading_strategy
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
        ticker_24h = binance_client.get_ticker(symbol='BTCUSDT')
        depth = binance_client.get_order_book(symbol='BTCUSDT')
        
        # 获取K线数据
        klines_1d = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1DAY,
            limit=90
        )
        
        klines_4h = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_4HOUR,
            limit=120
        )
        
        klines_1h = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1HOUR,
            limit=168
        )
        
        # 获取历史策略和分析
        recent_strategies = get_recent_strategies(limit=5)
        recent_analysis = get_recent_market_analysis(limit=5)
        
        # 转换策略数据为JSON格式
        history_strategies = []
        for strategy in recent_strategies:
            history_strategies.append({
                'timestamp': strategy.timestamp.isoformat(),
                'action': strategy.action,
                'entry_price': strategy.entry_price,
                'stop_loss': strategy.stop_loss,
                'take_profit': strategy.take_profit,
                'risk_level': strategy.risk_level,
                'reasoning': strategy.reasoning
            })
            
        # 转换分析数据为JSON格式
        history_analysis = []
        for analysis in recent_analysis:
            history_analysis.append({
                'timestamp': analysis.timestamp.isoformat(),
                'market_trend': analysis.market_trend,
                'market_sentiment': analysis.market_sentiment,
                'confidence': analysis.confidence
            })
        
        logger.debug(f"获取到 {len(klines_1d)} 根日线数据")
        logger.debug(f"获取到 {len(klines_4h)} 根4小时线数据")
        logger.debug(f"获取到 {len(klines_1h)} 根小时线数据")
        
        if len(klines_1d) < 26:  # MACD需要26天数据
            logger.warning(f"日线数据不足，当前只有 {len(klines_1d)} 根K线")
        
        # 计算技术指标
        rsi_values = {
            '1d': calculate_rsi(klines_1d),
            '4h': calculate_rsi(klines_4h),
            '1h': calculate_rsi(klines_1h)
        }
        
        macd_values = {
            '1d': calculate_macd(klines_1d),
            '4h': calculate_macd(klines_4h),
            '1h': calculate_macd(klines_1h)
        }
        
        bollinger_values = {
            '1d': calculate_bollinger_position(klines_1d),
            '4h': calculate_bollinger_position(klines_4h),
            '1h': calculate_bollinger_position(klines_1h)
        }
        
        # 计算价格趋势
        price_trends = calculate_price_trends(klines_1d, klines_4h, klines_1h)
        
        logger.info(f"技术指标计算结果 - RSI: {rsi_values}, MACD: {macd_values}, 布林带位置: {bollinger_values}")
        logger.info(f"价格趋势分析: {price_trends}")
        
        # 计算24小时成交量变化
        current_volume = float(ticker_24h['volume'])
        previous_volume = float(klines_1d[-2][5]) if len(klines_1d) >= 2 else current_volume
        volume_change_24h = ((current_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
        
        market_data = {
            'symbol': 'BTCUSDT',
            'price': float(ticker['price']),
            'price_change_24h': float(ticker_24h['priceChangePercent']),
            'volume_24h': current_volume,
            'quote_volume': float(ticker_24h['quoteVolume']),
            'base_volume': current_volume,
            'volume_change_24h': round(volume_change_24h, 2),
            'buy_volume': sum(float(bid[1]) for bid in depth['bids'][:10]),
            'sell_volume': sum(float(ask[1]) for ask in depth['asks'][:10]),
            'rsi': rsi_values,
            'macd': macd_values,
            'bollinger_position': bollinger_values,
            'price_trends': price_trends
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
                'strategy': strategy,
                'history_strategies': history_strategies,
                'history_analysis': history_analysis
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_price_trends(klines_1d, klines_4h, klines_1h):
    """
    计算多个时间维度的价格趋势
    """
    try:
        # 计算MA20和MA50
        def calculate_ma(klines, period):
            if len(klines) < period:
                return None
            closes = [float(k[4]) for k in klines[-period:]]
            return sum(closes) / period
            
        trends = {
            '1d': {
                'ma20': calculate_ma(klines_1d, 20),
                'ma50': calculate_ma(klines_1d, 50),
                'high_30d': max([float(k[2]) for k in klines_1d[-30:]]),
                'low_30d': min([float(k[3]) for k in klines_1d[-30:]]),
            },
            '4h': {
                'ma20': calculate_ma(klines_4h, 20),
                'ma50': calculate_ma(klines_4h, 50),
                'high_7d': max([float(k[2]) for k in klines_4h[-42:]]),  # 42个4小时为7天
                'low_7d': min([float(k[3]) for k in klines_4h[-42:]]),
            },
            '1h': {
                'ma20': calculate_ma(klines_1h, 20),
                'ma50': calculate_ma(klines_1h, 50),
                'high_24h': max([float(k[2]) for k in klines_1h[-24:]]),
                'low_24h': min([float(k[3]) for k in klines_1h[-24:]]),
            }
        }
        
        # 添加趋势判断
        current_price = float(klines_1d[-1][4])
        for timeframe in trends:
            if trends[timeframe]['ma20'] and trends[timeframe]['ma50']:
                trends[timeframe]['trend'] = 'bullish' if trends[timeframe]['ma20'] > trends[timeframe]['ma50'] else 'bearish'
                trends[timeframe]['price_position'] = 'above_ma20' if current_price > trends[timeframe]['ma20'] else 'below_ma20'
                
        return trends
    except Exception as e:
        logger.error(f"价格趋势计算失败: {str(e)}", exc_info=True)
        return None

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = request.json
    # TODO: 实现实际的交易逻辑
    return jsonify({
        'success': True,
        'message': '交易提交成功',
        'order_id': '123456789'
    })

@app.route('/api/place_order', methods=['POST'])
def place_order():
    try:
        order_data = request.get_json()
        logger.info(f"收到下单请求: {order_data}")
        
        # 验证订单数据
        required_fields = ['symbol', 'side', 'type', 'price', 'quantity', 'stopLoss', 'takeProfit']
        for field in required_fields:
            if field not in order_data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        # 获取当前价格进行验证
        ticker = binance_client.get_symbol_ticker(symbol=order_data['symbol'])
        current_price = float(ticker['price'])
        
        # 计算价格偏差百分比
        price_deviation = abs(float(order_data['price']) - current_price) / current_price * 100
        
        # 如果价格偏差超过2%，拒绝下单
        if price_deviation > 2:
            return jsonify({
                'success': False,
                'message': f'当前市价与建议入场价格偏差过大 ({price_deviation:.2f}%)，为保护您的资金安全，已取消下单'
            }), 400
            
        # 创建限价单
        try:
            # 创建主订单
            order = binance_client.create_order(
                symbol=order_data['symbol'],
                side=order_data['side'],
                type=order_data['type'],
                timeInForce='GTC',
                quantity=order_data['quantity'],
                price=order_data['price']
            )
            
            # 如果主订单创建成功，添加止损单
            if order['orderId']:
                stop_loss_order = binance_client.create_order(
                    symbol=order_data['symbol'],
                    side='SELL' if order_data['side'] == 'BUY' else 'BUY',
                    type='STOP_LOSS_LIMIT',
                    timeInForce='GTC',
                    quantity=order_data['quantity'],
                    stopPrice=order_data['stopLoss'],
                    price=order_data['stopLoss']
                )
                
                # 添加止盈单
                take_profit_order = binance_client.create_order(
                    symbol=order_data['symbol'],
                    side='SELL' if order_data['side'] == 'BUY' else 'BUY',
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=order_data['quantity'],
                    price=order_data['takeProfit']
                )
                
                logger.info(f"下单成功 - 订单ID: {order['orderId']}, 止损单ID: {stop_loss_order['orderId']}, 止盈单ID: {take_profit_order['orderId']}")
                
                return jsonify({
                    'success': True,
                    'data': {
                        'orderId': order['orderId'],
                        'stopLossOrderId': stop_loss_order['orderId'],
                        'takeProfitOrderId': take_profit_order['orderId']
                    },
                    'message': '下单成功'
                })
                
        except Exception as e:
            logger.error(f"下单失败: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'下单失败: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"处理下单请求时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'系统错误: {str(e)}'
        }), 500

@app.route('/api/market_data', methods=['GET'])
def get_market_data():
    try:
        # 获取市场数据
        ticker = binance_client.get_symbol_ticker(symbol="BTCUSDT")
        ticker_24h = binance_client.get_ticker(symbol='BTCUSDT')
        depth = binance_client.get_order_book(symbol='BTCUSDT')
        
        # 获取K线数据
        klines_1d = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1DAY,
            limit=90
        )
        
        klines_4h = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_4HOUR,
            limit=120
        )
        
        klines_1h = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1HOUR,
            limit=168
        )
        
        # 计算技术指标
        rsi_values = {
            '1d': calculate_rsi(klines_1d),
            '4h': calculate_rsi(klines_4h),
            '1h': calculate_rsi(klines_1h)
        }
        
        macd_values = {
            '1d': calculate_macd(klines_1d),
            '4h': calculate_macd(klines_4h),
            '1h': calculate_macd(klines_1h)
        }
        
        bollinger_values = {
            '1d': calculate_bollinger_position(klines_1d),
            '4h': calculate_bollinger_position(klines_4h),
            '1h': calculate_bollinger_position(klines_1h)
        }
        
        # 计算价格趋势
        price_trends = calculate_price_trends(klines_1d, klines_4h, klines_1h)
        
        # 计算成交量变化
        current_volume = float(ticker_24h['volume'])
        previous_volume = float(klines_1d[-2][5]) if len(klines_1d) >= 2 else current_volume
        volume_change_24h = ((current_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
        
        market_data = {
            'symbol': 'BTCUSDT',
            'price': float(ticker['price']),
            'price_change_24h': float(ticker_24h['priceChangePercent']),
            'volume_24h': current_volume,
            'quote_volume': float(ticker_24h['quoteVolume']),
            'base_volume': current_volume,
            'volume_change_24h': round(volume_change_24h, 2),
            'buy_volume': sum(float(bid[1]) for bid in depth['bids'][:10]),
            'sell_volume': sum(float(ask[1]) for ask in depth['asks'][:10]),
            'rsi': rsi_values,
            'macd': macd_values,
            'bollinger_position': bollinger_values,
            'price_trends': price_trends
        }
        
        return jsonify({
            'success': True,
            'data': market_data
        })
        
    except Exception as e:
        logger.error(f"获取市场数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recent-strategies', methods=['GET'])
def get_strategies():
    """获取最近的交易策略"""
    try:
        strategies = get_recent_strategies()
        return jsonify({"success": True, "data": strategies})
    except Exception as e:
        logger.error(f"获取最近交易策略时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/recent-analysis', methods=['GET'])
def get_analysis():
    """获取最近的市场分析"""
    try:
        analysis = get_recent_market_analysis()
        return jsonify({"success": True, "data": analysis})
    except Exception as e:
        logger.error(f"获取最近市场分析时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/save-analysis', methods=['POST'])
def save_analysis():
    """保存市场分析"""
    try:
        data = request.json
        analysis_text = data.get('analysis')
        if not analysis_text:
            return jsonify({"success": False, "error": "分析内容不能为空"}), 400
        
        save_market_analysis(analysis_text)
        return jsonify({"success": True, "message": "市场分析保存成功"})
    except Exception as e:
        logger.error(f"保存市场分析时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/save-strategy', methods=['POST'])
def save_strategy():
    """保存交易策略"""
    try:
        data = request.json
        strategy_text = data.get('strategy')
        if not strategy_text:
            return jsonify({"success": False, "error": "策略内容不能为空"}), 400
        
        save_trading_strategy(strategy_text)
        return jsonify({"success": True, "message": "交易策略保存成功"})
    except Exception as e:
        logger.error(f"保存交易策略时出错: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/position', methods=['GET'])
def get_position_info():
    """获取当前仓位信息"""
    try:
        position = get_current_position()
        if position:
            # 获取当前市场价格
            ticker = binance_client.get_symbol_ticker(symbol="BTCUSDT")
            current_price = float(ticker['price'])
            
            # 计算盈亏
            if position.side == 'LONG':
                pnl = (current_price - position.entry_price) * position.quantity
            else:  # SHORT
                pnl = (position.entry_price - current_price) * position.quantity
            
            # 计算盈亏百分比
            pnl_percentage = (pnl / (position.entry_price * position.quantity)) * 100
            
            return jsonify({
                'success': True,
                'data': {
                    'symbol': position.symbol,
                    'side': position.side,
                    'entry_price': position.entry_price,
                    'current_price': current_price,
                    'quantity': position.quantity,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'pnl': round(pnl, 2),
                    'pnl_percentage': round(pnl_percentage, 2),
                    'entry_time': position.entry_time.isoformat(),
                    'status': position.status
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': None
            })
    except Exception as e:
        logger.error(f"获取仓位信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/position/history', methods=['GET'])
def get_position_history_api():
    """获取历史仓位记录"""
    try:
        positions = get_position_history(limit=10)
        history = []
        for pos in positions:
            history.append({
                'symbol': pos.symbol,
                'side': pos.side,
                'entry_price': pos.entry_price,
                'quantity': pos.quantity,
                'stop_loss': pos.stop_loss,
                'take_profit': pos.take_profit,
                'pnl': pos.pnl,
                'entry_time': pos.entry_time.isoformat(),
                'close_time': pos.close_time.isoformat() if pos.close_time else None,
                'close_price': pos.close_price,
                'status': pos.status
            })
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        logger.error(f"获取历史仓位记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/logs', methods=['GET'])
def get_recent_logs():
    """获取最近的日志记录"""
    try:
        with open('auto_trader.log', 'r') as f:
            # 读取最后1000行日志
            lines = f.readlines()[-1000:]
            return jsonify({
                'success': True,
                'data': lines
            })
    except Exception as e:
        logger.error(f"获取日志记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 