from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
from pathlib import Path
import logging
import numpy as np
from typing import List, Union
import asyncio
# from services.trader.trading_system import TradingSystem

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

trading_system = None

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# @app.before_first_request
# def init_trading_system():
#     global trading_system
#     if trading_system is None:
#         trading_system = TradingSystem()
#         logger.info("Trading system initialized")

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

@app.route('/position')
def position():
    return render_template('position.html')

@app.route('/strategy')
def strategy():
    return render_template('strategy.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/system/status')
def system_status():
    """获取系统状态"""
    try:
        # 检查交易系统状态
        system_ok = trading_system and trading_system.is_running()
        # 检查数据连接状态
        data_ok = trading_system and trading_system.check_data_connection()
        # 检查交易连接状态
        trade_ok = trading_system and trading_system.check_trade_connection()
        
        if not system_ok:
            return jsonify({
                "status": "error",
                "message": "交易系统未运行"
            })
        elif not data_ok or not trade_ok:
            return jsonify({
                "status": "warning",
                "message": "部分服务异常" + 
                          (", 数据连接断开" if not data_ok else "") +
                          (", 交易连接断开" if not trade_ok else "")
            })
        else:
            return jsonify({
                "status": "success",
                "message": "系统正常运行"
            })
    except Exception as e:
        logger.error(f"系统状态检查失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"系统状态检查失败: {str(e)}"
        })

@app.route('/api/positions')
def get_positions():
    """获取所有持仓信息"""
    try:
        positions = run_async(trading_system.get_positions())
        return jsonify({
            "status": "success",
            "data": positions
        })
    except Exception as e:
        logger.error(f"获取持仓信息失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/positions/<int:position_id>', methods=['PUT'])
def update_position(position_id):
    """更新持仓信息"""
    try:
        data = request.get_json()
        result = run_async(trading_system.update_position(
            position_id,
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit')
        ))
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        logger.error(f"更新持仓失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/positions/<int:position_id>/close', methods=['POST'])
def close_position(position_id):
    """关闭持仓"""
    try:
        data = request.get_json()
        result = run_async(trading_system.close_position(
            position_id,
            reason=data.get('reason', '手动平仓')
        ))
        return jsonify({
            "status": "success",
            "data": result
        })
    except Exception as e:
        logger.error(f"关闭持仓失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/portfolio')
def get_portfolio():
    """获取投资组合信息"""
    try:
        portfolio = run_async(trading_system.get_portfolio())
        return jsonify({
            "status": "success",
            "data": portfolio
        })
    except Exception as e:
        logger.error(f"获取投资组合信息失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/trade_history')
def get_trade_history():
    """获取交易历史"""
    try:
        history = run_async(trading_system.get_trade_history())
        return jsonify({
            "status": "success",
            "data": history
        })
    except Exception as e:
        logger.error(f"获取交易历史失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

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
        
        # 获取多个时间维度的K线数据
        klines_1d = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1DAY,
            limit=90  # 获取90天的日线数据
        )
        
        klines_4h = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_4HOUR,
            limit=120  # 获取最近20天的4小时数据
        )
        
        klines_1h = binance_client.get_klines(
            symbol="BTCUSDT", 
            interval=Client.KLINE_INTERVAL_1HOUR,
            limit=168  # 获取最近7天的小时数据
        )
        
        logger.debug(f"获取到 {len(klines_1d)} 根日线数据")
        logger.debug(f"获取到 {len(klines_4h)} 根4小时线数据")
        logger.debug(f"获取到 {len(klines_1h)} 根小时线数据")
        
        if len(klines_1d) < 26:  # MACD需要26天数据
            logger.warning(f"日线数据不足，当前只有 {len(klines_1d)} 根K线")
            
        depth = binance_client.get_order_book(symbol='BTCUSDT')
        
        # 获取24小时统计数据
        ticker_24h = binance_client.get_ticker(symbol='BTCUSDT')
        
        # 计算多个时间维度的技术指标
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
        
        # 计算成交量变化百分比
        volume_change_24h = ((current_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
        
        # 计算7天平均成交量和当前成交量的对比
        avg_volume_7d = sum(float(k[5]) for k in klines_1d[-7:]) / 7 if len(klines_1d) >= 7 else current_volume
        volume_vs_avg = ((current_volume - avg_volume_7d) / avg_volume_7d * 100) if avg_volume_7d > 0 else 0
        
        logger.info(f"成交量分析 - 当前: {current_volume:.2f}, 24h变化: {volume_change_24h:.2f}%, 7日均量对比: {volume_vs_avg:.2f}%")
        
        market_data = {
            'symbol': 'BTCUSDT',
            'price': float(ticker['price']),
            'price_change_24h': float(ticker_24h['priceChangePercent']),
            'volume_24h': current_volume,
            'quote_volume': float(ticker_24h['quoteVolume']),
            'base_volume': current_volume,
            'volume_change_24h': round(volume_change_24h, 2),
            'volume_vs_7d_avg': round(volume_vs_avg, 2),
            'buy_volume': sum(float(bid[1]) for bid in depth['bids'][:10]),
            'sell_volume': sum(float(ask[1]) for ask in depth['asks'][:10]),
            'buy_depth': depth['bids'][:5],
            'sell_depth': depth['asks'][:5],
            'rsi': rsi_values,
            'macd': macd_values,
            'bollinger_position': bollinger_values,
            'price_trends': price_trends
        }
        
        # 使用 GPT 模型分析市场
        analysis_result = run_async(gpt_model.analyze_market(market_data))
        
        # 生成交易策略
        strategy = run_async(gpt_model.generate_strategy(analysis_result))
        
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

if __name__ == '__main__':
    # 允许局域网访问，设置host为0.0.0.0
    host = '0.0.0.0'
    port = 5000
    logger.info(f"服务器将在 {host}:{port} 启动，允许局域网访问")
    app.run(debug=True, host=host, port=port) 