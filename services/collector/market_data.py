import asyncio
import logging
from datetime import datetime
from typing import List, Dict

from binance import AsyncClient
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class MarketDataCollector:
    def __init__(self, api_key: str, api_secret: str, trading_pairs: List[str]):
        """
        初始化市场数据采集器
        
        Args:
            api_key: Binance API密钥
            api_secret: Binance API密钥
            trading_pairs: 交易对列表，如 ["BTCUSDT", "ETHUSDT"]
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.trading_pairs = trading_pairs
        self.client = None
        self.is_running = False
        
    async def initialize(self):
        """
        初始化Binance客户端
        """
        try:
            self.client = await AsyncClient.create(self.api_key, self.api_secret)
            logger.info("Binance客户端初始化成功")
        except BinanceAPIException as e:
            logger.error(f"Binance客户端初始化失败: {e}")
            raise
            
    async def get_real_time_price(self, symbol: str) -> Dict:
        """
        获取实时价格数据
        
        Args:
            symbol: 交易对名称，如 "BTCUSDT"
            
        Returns:
            Dict: 包含价格信息的字典
        """
        try:
            ticker = await self.client.get_symbol_ticker(symbol=symbol)
            return {
                "symbol": symbol,
                "price": float(ticker["price"]),
                "timestamp": datetime.now().isoformat()
            }
        except BinanceAPIException as e:
            logger.error(f"获取{symbol}实时价格失败: {e}")
            return None
            
    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对名称
            interval: K线间隔，如 "1m", "5m", "1h"
            limit: 获取的K线数量
            
        Returns:
            List[Dict]: K线数据列表
        """
        try:
            klines = await self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            return [{
                "symbol": symbol,
                "open_time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": k[6],
                "quote_volume": float(k[7]),
                "trades": int(k[8])
            } for k in klines]
        except BinanceAPIException as e:
            logger.error(f"获取{symbol} K线数据失败: {e}")
            return []
            
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对名称
            limit: 订单簿深度
            
        Returns:
            Dict: 订单簿数据
        """
        try:
            depth = await self.client.get_order_book(symbol=symbol, limit=limit)
            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "bids": [[float(price), float(qty)] for price, qty in depth["bids"]],
                "asks": [[float(price), float(qty)] for price, qty in depth["asks"]]
            }
        except BinanceAPIException as e:
            logger.error(f"获取{symbol}订单簿数据失败: {e}")
            return None
            
    async def start_data_collection(self):
        """
        启动数据采集
        """
        self.is_running = True
        while self.is_running:
            try:
                for symbol in self.trading_pairs:
                    # 获取实时价格
                    price_data = await self.get_real_time_price(symbol)
                    if price_data:
                        # TODO: 将数据保存到数据库
                        logger.info(f"收集到{symbol}价格数据: {price_data['price']}")
                    
                    # 获取K线数据
                    klines = await self.get_klines(symbol, "1m", 1)
                    if klines:
                        # TODO: 将数据保存到数据库
                        logger.info(f"收集到{symbol} K线数据")
                    
                    # 获取订单簿数据
                    order_book = await self.get_order_book(symbol)
                    if order_book:
                        # TODO: 将数据保存到数据库
                        logger.info(f"收集到{symbol}订单簿数据")
                        
                await asyncio.sleep(1)  # 控制请求频率
                
            except Exception as e:
                logger.error(f"数据采集过程中出错: {e}")
                await asyncio.sleep(5)  # 发生错误时等待较长时间
                
    async def stop_data_collection(self):
        """
        停止数据采集
        """
        self.is_running = False
        if self.client:
            await self.client.close_connection()
            logger.info("数据采集服务已停止") 