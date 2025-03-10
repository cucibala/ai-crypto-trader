import logging
from typing import Dict, Optional
from datetime import datetime
import asyncio

from binance import AsyncClient
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class TradingExecutor:
    def __init__(self, 
                 api_key: str,
                 api_secret: str,
                 max_position_size: float,
                 risk_limit_percentage: float,
                 stop_loss_percentage: float):
        """
        初始化交易执行器
        
        Args:
            api_key: Binance API密钥
            api_secret: Binance API密钥
            max_position_size: 最大持仓量（USDT）
            risk_limit_percentage: 风险限制百分比
            stop_loss_percentage: 止损百分比
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.max_position_size = max_position_size
        self.risk_limit_percentage = risk_limit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.client = None
        self.active_orders = {}
        
    async def initialize(self):
        """
        初始化Binance客户端
        """
        try:
            self.client = await AsyncClient.create(self.api_key, self.api_secret)
            logger.info("交易执行器初始化成功")
        except BinanceAPIException as e:
            logger.error(f"交易执行器初始化失败: {e}")
            raise
            
    async def execute_trade(self, 
                          symbol: str,
                          side: str,
                          quantity: float,
                          price: Optional[float] = None) -> Dict:
        """
        执行交易
        
        Args:
            symbol: 交易对
            side: 交易方向 (BUY/SELL)
            quantity: 交易数量
            price: 限价单价格（可选，为None时为市价单）
            
        Returns:
            Dict: 订单信息
        """
        try:
            # 检查风险限制
            if not await self._check_risk_limits(symbol, quantity, price):
                raise ValueError("交易超出风险限制")
                
            # 创建订单
            order_params = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity
            }
            
            if price:
                order_params["type"] = "LIMIT"
                order_params["price"] = price
                order_params["timeInForce"] = "GTC"
            else:
                order_params["type"] = "MARKET"
                
            order = await self.client.create_order(**order_params)
            
            # 记录活动订单
            self.active_orders[order["orderId"]] = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "status": order["status"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"订单执行成功: {order}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"订单执行失败: {e}")
            return {"error": str(e)}
            
    async def _check_risk_limits(self, 
                                symbol: str,
                                quantity: float,
                                price: Optional[float]) -> bool:
        """
        检查风险限制
        """
        try:
            # 获取账户信息
            account = await self.client.get_account()
            total_balance = sum(
                float(balance["free"]) * float(await self._get_asset_price(balance["asset"]))
                for balance in account["balances"]
                if float(balance["free"]) > 0
            )
            
            # 计算订单价值
            if price:
                order_value = quantity * price
            else:
                current_price = float((await self.client.get_symbol_ticker(symbol=symbol))["price"])
                order_value = quantity * current_price
                
            # 检查是否超过最大持仓限制
            if order_value > self.max_position_size:
                logger.warning(f"订单价值 {order_value} 超过最大持仓限制 {self.max_position_size}")
                return False
                
            # 检查是否超过风险限制
            if order_value > total_balance * (self.risk_limit_percentage / 100):
                logger.warning(f"订单价值 {order_value} 超过风险限制")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return False
            
    async def _get_asset_price(self, asset: str) -> float:
        """
        获取资产价格（以USDT计价）
        """
        if asset == "USDT":
            return 1.0
            
        try:
            symbol = f"{asset}USDT"
            price = await self.client.get_symbol_ticker(symbol=symbol)
            return float(price["price"])
        except:
            return 0.0
            
    async def place_stop_loss(self, 
                             symbol: str,
                             side: str,
                             quantity: float,
                             stop_price: float) -> Dict:
        """
        设置止损单
        """
        try:
            order = await self.client.create_order(
                symbol=symbol,
                side="SELL" if side == "BUY" else "BUY",
                type="STOP_LOSS_LIMIT",
                quantity=quantity,
                stopPrice=stop_price,
                price=stop_price,  # 止损价格
                timeInForce="GTC"
            )
            
            logger.info(f"止损单设置成功: {order}")
            return order
            
        except BinanceAPIException as e:
            logger.error(f"止损单设置失败: {e}")
            return {"error": str(e)}
            
    async def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """
        取消订单
        """
        try:
            result = await self.client.cancel_order(
                symbol=symbol,
                orderId=order_id
            )
            
            if order_id in self.active_orders:
                del self.active_orders[order_id]
                
            logger.info(f"订单取消成功: {result}")
            return result
            
        except BinanceAPIException as e:
            logger.error(f"订单取消失败: {e}")
            return {"error": str(e)}
            
    async def get_order_status(self, symbol: str, order_id: str) -> Dict:
        """
        获取订单状态
        """
        try:
            order = await self.client.get_order(
                symbol=symbol,
                orderId=order_id
            )
            
            if order_id in self.active_orders:
                self.active_orders[order_id]["status"] = order["status"]
                
            return order
            
        except BinanceAPIException as e:
            logger.error(f"获取订单状态失败: {e}")
            return {"error": str(e)}
            
    async def monitor_orders(self):
        """
        监控活动订单
        """
        while True:
            try:
                for order_id, order_info in list(self.active_orders.items()):
                    status = await self.get_order_status(
                        order_info["symbol"],
                        order_id
                    )
                    
                    if status.get("status") in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                        del self.active_orders[order_id]
                        
                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"订单监控出错: {e}")
                await asyncio.sleep(5)  # 发生错误时等待较长时间 