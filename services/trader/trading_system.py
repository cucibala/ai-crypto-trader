import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

from config.settings import RISK_MANAGEMENT, TRADING_PAIRS
from utils.binance_client import BinanceClient
from services.analyzer.social_media_analyzer import SocialMediaAnalyzer

logger = logging.getLogger(__name__)

class TradingSystem:
    """交易系统核心类"""
    
    def __init__(self):
        """初始化交易系统"""
        self.client = BinanceClient()
        self.social_analyzer = SocialMediaAnalyzer()
        self.active_orders = {}  # 活跃订单
        self.positions = {}      # 当前持仓
        self.trade_history = []  # 交易历史
        
        # 风险管理参数
        self.max_position_size = RISK_MANAGEMENT['max_position_size']
        self.risk_limit_percentage = RISK_MANAGEMENT['risk_limit_percentage']
        self.stop_loss_percentage = RISK_MANAGEMENT['stop_loss_percentage']
        self.max_trades_per_day = RISK_MANAGEMENT['max_trades_per_day']
        
        # 交易统计
        self.daily_trades_count = 0
        self.total_pnl = Decimal('0')
        
    async def start(self):
        """启动交易系统"""
        try:
            # 初始化连接
            await self.client.connect()
            
            # 加载当前持仓和订单
            await self._load_current_state()
            
            # 启动市场监控
            await self._start_market_monitor()
            
            logger.info("交易系统启动成功")
            
        except Exception as e:
            logger.error(f"交易系统启动失败: {str(e)}")
            raise
            
    async def _load_current_state(self):
        """加载当前账户状态"""
        try:
            # 获取账户信息
            timestamp = int(datetime.now().timestamp() * 1000)
            params = {
                "apiKey": self.client.api_key,
                "timestamp": timestamp
            }
            params["signature"] = self.client.generate_signature(params)
            account_info = await self.client._send_request(
                method="account.status",
                params=params
            )
            
            # 更新持仓信息
            balances = account_info.get('balances', [])
            for balance in balances:
                asset = balance['asset']
                free = Decimal(balance['free'])
                locked = Decimal(balance['locked'])
                if free > 0 or locked > 0:
                    self.positions[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    }
                    
            # 获取当前挂单
            timestamp = int(datetime.now().timestamp() * 1000)
            params = {
                "apiKey": self.client.api_key,
                "timestamp": timestamp
            }
            params["signature"] = self.client.generate_signature(params)
           
            open_orders = await self.client._send_request(
                method="openOrders.status",
                params=params
            )
            
            for order in open_orders:
                self.active_orders[order['orderId']] = order
                
            logger.info(f"当前持仓: {self.positions}")
            logger.info(f"活跃订单数: {len(self.active_orders)}")
            
        except Exception as e:
            logger.error(f"加载账户状态失败: {str(e)}")
            raise
            
    async def _start_market_monitor(self):
        """启动市场监控"""
        for symbol in TRADING_PAIRS:
            asyncio.create_task(self._monitor_symbol(symbol))
            
    async def _monitor_symbol(self, symbol: str):
        """监控单个交易对"""
        while True:
            try:
                # 获取市场数据
                price_info = await self.client._send_request(
                    method="ticker.price",
                    params={"symbol": symbol}  # 行情接口不需要签名
                )
                current_price = Decimal(price_info['price'])
                
                # 检查止损条件
                await self._check_stop_loss(symbol, current_price)
                
                # 更新持仓价值
                await self._update_position_value(symbol, current_price)
                
                # 等待下一次更新
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"监控{symbol}失败: {str(e)}")
                await asyncio.sleep(5)
                
    async def place_order(self, 
                         symbol: str,
                         side: str,
                         order_type: str,
                         quantity: Decimal,
                         price: Optional[Decimal] = None) -> Dict:
        """下单"""
        try:
            # 风险检查
            if not self._check_risk_limits(symbol, side, quantity, price):
                raise ValueError("订单超出风险限制")
                
            # 处理价格和数量的精度
            if symbol == "DOGEUSDT":
                quantity = quantity.quantize(Decimal('1'))  # DOGE 使用整数
                if price:
                    price = price.quantize(Decimal('0.000001'))  # 价格6位小数
                
            # 构建订单参数
            timestamp = int(datetime.now().timestamp() * 1000)
            params = {
                "apiKey": self.client.api_key,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": str(quantity),
                "timestamp": timestamp
            }
            if order_type == "LIMIT":
                if not price:
                    raise ValueError("限价单必须指定价格")
                params["price"] = str(price)
                params["timeInForce"] = "GTC"
            print(params)

            # 生成签名
            params["signature"] = self.client.generate_signature(params)
                
            # 发送订单
            order = await self.client._send_request(
                method="order.test",  # 使用正确的方法名
                params=params
            )
            
            # 更新活跃订单
            self.active_orders[order['orderId']] = order
            
            # 更新交易统计
            self.daily_trades_count += 1
            
            logger.info("下单成功: %s", order)
            return order
            
        except Exception as e:
            logger.error("下单失败: %s", str(e))
            raise
            
    async def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """取消订单"""
        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            params = {
                "apiKey": self.client.api_key,
                "symbol": symbol,
                "orderId": order_id,
                "timestamp": timestamp
            }
            params["signature"] = self.client.generate_signature(params)
            
            result = await self.client._send_request(
                method="order.cancel",
                params=params
            )
            
            # 从活跃订单中移除
            if order_id in self.active_orders:
                del self.active_orders[order_id]
                
            logger.info(f"取消订单成功: {result}")
            return result
            
        except Exception as e:
            logger.error(f"取消订单失败: {str(e)}")
            raise
            
    def _check_risk_limits(self, 
                          symbol: str, 
                          side: str, 
                          quantity: Decimal,
                          price: Optional[Decimal]) -> bool:
        """
        检查风险限制
        
        Returns:
            bool: 是否通过风险检查
        """
        # 检查日交易次数
        if self.daily_trades_count >= self.max_trades_per_day:
            logger.warning("超出每日最大交易次数限制")
            return False
            
        # 检查持仓规模
        position_value = quantity * price if price else quantity
        if position_value > self.max_position_size:
            logger.warning("超出最大持仓规模限制")
            return False
            
        # 检查风险敞口
        total_exposure = sum(
            pos['total'] for pos in self.positions.values()
        )
        if total_exposure * Decimal(str(1 + self.risk_limit_percentage/100)) < position_value:
            logger.warning("超出风险敞口限制")
            return False
            
        return True
        
    async def _check_stop_loss(self, symbol: str, current_price: Decimal):
        """检查止损条件"""
        if symbol in self.positions:
            position = self.positions[symbol]
            if position['total'] > 0:
                # 计算浮动盈亏
                entry_price = position.get('entry_price', current_price)
                pnl_percentage = (current_price - entry_price) / entry_price * 100
                
                # 检查止损条件
                if pnl_percentage <= -self.stop_loss_percentage:
                    logger.warning(f"{symbol}触发止损: {pnl_percentage}%")
                    await self.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="MARKET",
                        quantity=position['total']
                    )
                    
    async def _update_position_value(self, symbol: str, current_price: Decimal):
        """更新持仓价值"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position['current_price'] = current_price
            position['value'] = position['total'] * current_price
            
    async def get_account_summary(self) -> Dict:
        """获取账户摘要"""
        try:
            total_value = Decimal('0')
            position_summary = []
            
            # 获取最新价格并计算总价值
            for symbol, position in self.positions.items():
                if position['total'] > 0:
                    # USDT 不需要获取价格，直接使用面值
                    if symbol == 'USDT':
                        current_price = Decimal('1')
                    else:
                        # 对非 USDT 资产获取价格
                        price_info = await self.client._send_request(
                            method="ticker.price",
                            params={"symbol": f"{symbol}USDT"}
                        )
                        current_price = Decimal(price_info['price'])
                        
                    value = position['total'] * current_price
                    total_value += value
                    
                    position_summary.append({
                        'asset': symbol,
                        'total': str(position['total']),
                        'free': str(position['free']),
                        'locked': str(position['locked']),
                        'current_price': str(current_price),
                        'value': str(value)
                    })
                    
            return {
                'total_value': str(total_value),
                'total_pnl': str(self.total_pnl),
                'daily_trades_count': self.daily_trades_count,
                'active_orders_count': len(self.active_orders),
                'positions': position_summary,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取账户摘要失败: {str(e)}")
            raise 