import time
import logging
from datetime import datetime
import json
from typing import Dict, List, Optional
from models.database import (
    get_current_position, create_position, update_position, 
    close_position, save_market_analysis, save_trading_strategy
)
from models.gpt_model import GPTModel
from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class AutoTrader:
    def __init__(self, binance_client: Client, gpt_model: GPTModel):
        self.binance_client = binance_client
        self.gpt_model = gpt_model
        self.symbol = "BTCUSDT"
        self.check_interval = 300  # 5分钟检查一次
        
    async def get_market_data(self) -> Dict:
        """获取市场数据"""
        try:
            ticker = self.binance_client.get_symbol_ticker(symbol=self.symbol)
            ticker_24h = self.binance_client.get_ticker(symbol=self.symbol)
            depth = self.binance_client.get_order_book(symbol=self.symbol)
            
            klines_1d = self.binance_client.get_klines(
                symbol=self.symbol,
                interval=Client.KLINE_INTERVAL_1DAY,
                limit=90
            )
            
            current_price = float(ticker['price'])
            
            market_data = {
                'symbol': self.symbol,
                'current_price': current_price,
                'price_change_24h': float(ticker_24h['priceChangePercent']),
                'volume_24h': float(ticker_24h['volume']),
                'quote_volume': float(ticker_24h['quoteVolume']),
                'timestamp': datetime.now().isoformat()
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {str(e)}")
            raise
    
    def calculate_position_pnl(self, position, current_price: float) -> float:
        """计算仓位盈亏"""
        if position.side == 'LONG':
            return (current_price - position.entry_price) * position.quantity
        else:  # SHORT
            return (position.entry_price - current_price) * position.quantity
    
    async def analyze_position_risk(self, position, market_data: Dict) -> Dict:
        """分析仓位风险"""
        conversation_history = json.loads(position.conversation_history)
        
        # 构建分析提示
        prompt = f"""
        基于以下信息分析当前仓位风险：
        
        当前仓位信息：
        - 方向: {position.side}
        - 入场价: {position.entry_price}
        - 数量: {position.quantity}
        - 止损价: {position.stop_loss}
        - 止盈价: {position.take_profit}
        
        市场数据：
        - 当前价格: {market_data['current_price']}
        - 24小时涨跌幅: {market_data['price_change_24h']}%
        - 24小时成交量: {market_data['volume_24h']}
        
        历史对话记录：
        {json.dumps(conversation_history, ensure_ascii=False, indent=2)}
        
        请分析：
        1. 当前仓位风险等级（低/中/高）
        2. 是否需要调整止损或止盈
        3. 是否需要平仓
        4. 具体建议操作
        """
        
        analysis = await self.gpt_model.analyze_position(prompt)
        return analysis
    
    async def execute_trade(self, action: str, params: Dict) -> bool:
        """执行交易操作"""
        try:
            if action == 'OPEN_LONG':
                order = self.binance_client.create_order(
                    symbol=self.symbol,
                    side='BUY',
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=params['quantity'],
                    price=params['price']
                )
                
                # 设置止损和止盈订单
                if params.get('stop_loss'):
                    self.binance_client.create_order(
                        symbol=self.symbol,
                        side='SELL',
                        type='STOP_LOSS_LIMIT',
                        timeInForce='GTC',
                        quantity=params['quantity'],
                        price=params['stop_loss'],
                        stopPrice=params['stop_loss']
                    )
                
                if params.get('take_profit'):
                    self.binance_client.create_order(
                        symbol=self.symbol,
                        side='SELL',
                        type='LIMIT',
                        timeInForce='GTC',
                        quantity=params['quantity'],
                        price=params['take_profit']
                    )
                
            elif action == 'OPEN_SHORT':
                order = self.binance_client.create_order(
                    symbol=self.symbol,
                    side='SELL',
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=params['quantity'],
                    price=params['price']
                )
                
                # 设置止损和止盈订单
                if params.get('stop_loss'):
                    self.binance_client.create_order(
                        symbol=self.symbol,
                        side='BUY',
                        type='STOP_LOSS_LIMIT',
                        timeInForce='GTC',
                        quantity=params['quantity'],
                        price=params['stop_loss'],
                        stopPrice=params['stop_loss']
                    )
                
                if params.get('take_profit'):
                    self.binance_client.create_order(
                        symbol=self.symbol,
                        side='BUY',
                        type='LIMIT',
                        timeInForce='GTC',
                        quantity=params['quantity'],
                        price=params['take_profit']
                    )
                    
            elif action == 'CLOSE':
                side = 'SELL' if params['position_side'] == 'LONG' else 'BUY'
                order = self.binance_client.create_order(
                    symbol=self.symbol,
                    side=side,
                    type='MARKET',
                    quantity=params['quantity']
                )
                
            return True
            
        except BinanceAPIException as e:
            logger.error(f"交易执行失败: {str(e)}")
            return False
    
    async def run(self):
        """运行自动交易"""
        while True:
            try:
                # 获取市场数据
                market_data = await self.get_market_data()
                current_price = market_data['current_price']
                
                # 获取当前仓位
                position = get_current_position()
                
                if position is None:
                    # 没有仓位，使用GPT分析是否开仓
                    analysis = await self.gpt_model.analyze_market(market_data)
                    strategy = await self.gpt_model.generate_strategy(analysis)
                    
                    # 保存分析和策略
                    save_market_analysis(
                        analysis_text=analysis['analysis_text'],
                        market_trend=analysis['market_trend'],
                        market_sentiment=analysis['market_sentiment'],
                        confidence=analysis['confidence']
                    )
                    
                    save_trading_strategy(
                        strategy_text=strategy['reasoning'],
                        action=strategy['action'],
                        entry_price=strategy['entry_price'],
                        stop_loss=strategy['stop_loss'],
                        take_profit=strategy['take_profit'],
                        risk_level=strategy['risk_level']
                    )
                    
                    # 如果建议开仓，执行交易
                    if strategy['action'] in ['OPEN_LONG', 'OPEN_SHORT']:
                        success = await self.execute_trade(strategy['action'], {
                            'price': strategy['entry_price'],
                            'quantity': strategy['quantity'],
                            'stop_loss': strategy['stop_loss'],
                            'take_profit': strategy['take_profit']
                        })
                        
                        if success:
                            # 创建新仓位记录
                            create_position(
                                symbol=self.symbol,
                                side='LONG' if strategy['action'] == 'OPEN_LONG' else 'SHORT',
                                entry_price=strategy['entry_price'],
                                quantity=strategy['quantity'],
                                stop_loss=strategy['stop_loss'],
                                take_profit=strategy['take_profit'],
                                conversation_history=[{
                                    'market_data': market_data,
                                    'analysis': analysis,
                                    'strategy': strategy
                                }]
                            )
                
                else:
                    # 有仓位，分析风险并更新仓位
                    pnl = self.calculate_position_pnl(position, current_price)
                    
                    # 分析仓位风险
                    risk_analysis = await self.analyze_position_risk(position, market_data)
                    
                    # 更新对话历史
                    conversation_history = json.loads(position.conversation_history)
                    conversation_history.append({
                        'market_data': market_data,
                        'risk_analysis': risk_analysis,
                        'pnl': pnl
                    })
                    
                    # 更新仓位信息
                    update_position(
                        position.id,
                        conversation_history=json.dumps(conversation_history),
                        pnl=pnl
                    )
                    
                    # 如果需要平仓
                    if risk_analysis.get('should_close', False):
                        success = await self.execute_trade('CLOSE', {
                            'position_side': position.side,
                            'quantity': position.quantity
                        })
                        
                        if success:
                            close_position(position.id, current_price, pnl)
                    
                    # 如果需要调整止损止盈
                    elif risk_analysis.get('adjust_stops', False):
                        new_stop_loss = risk_analysis.get('new_stop_loss')
                        new_take_profit = risk_analysis.get('new_take_profit')
                        
                        if new_stop_loss or new_take_profit:
                            update_position(
                                position.id,
                                stop_loss=new_stop_loss or position.stop_loss,
                                take_profit=new_take_profit or position.take_profit
                            )
                
                # 等待下一次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"自动交易运行错误: {str(e)}", exc_info=True)
                time.sleep(60)  # 发生错误时等待1分钟后继续 