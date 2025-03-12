from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from models.gpt_model import GPTModel
from models.base_model import BaseModel
from config.settings import MODEL_CONFIG
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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
async def get_market_analysis():
    try:
        # 获取市场数据
        ticker = binance_client.get_symbol_ticker(symbol="BTCUSDT")
        klines = binance_client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_1DAY, limit=7)
        depth = binance_client.get_order_book(symbol='BTCUSDT')
        
        # 准备市场数据
        market_data = {
            'symbol': 'BTCUSDT',
            'price': float(ticker['price']),
            'price_change_24h': 0,  # 需要计算
            'volume_24h': sum(float(k[5]) for k in klines[-24:]) if len(klines) >= 24 else 0,
            'buy_volume': sum(float(bid[1]) for bid in depth['bids'][:10]),
            'sell_volume': sum(float(ask[1]) for ask in depth['asks'][:10]),
            'buy_depth': depth['bids'][:5],
            'sell_depth': depth['asks'][:5]
        }
        
        # 计算24小时价格变化
        if len(klines) >= 2:
            yesterday_price = float(klines[-2][4])  # 昨日收盘价
            current_price = float(ticker['price'])
            market_data['price_change_24h'] = ((current_price - yesterday_price) / yesterday_price) * 100
        
        # 使用 GPT 模型分析市场
        analysis_result = await gpt_model.analyze_market(market_data)
        
        # 生成交易策略
        strategy = await gpt_model.generate_strategy(analysis_result)
        
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