import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from models.database import Session, Kline, MarketData
from utils.binance_client import BinanceClient
from config.settings import TRADING_PAIRS

logger = logging.getLogger(__name__)

class DataCollector:
    """数据采集器"""
    
    def __init__(self, symbols: List[str] = None):
        """初始化数据采集器"""
        self.client = BinanceClient()
        self.symbols = symbols or TRADING_PAIRS
        self.is_running = False
        self.tasks = []
        
    async def start(self):
        """启动数据采集"""
        self.is_running = True
        await self.client.connect()  # 确保WebSocket连接已建立
        
        # 创建采集任务
        self.tasks = [
            asyncio.create_task(self._collect_klines(symbol)) for symbol in self.symbols
        ]
        self.tasks.append(asyncio.create_task(self._collect_market_data()))
        
        logger.info("数据采集器已启动")
        
    async def stop(self):
        """停止数据采集"""
        self.is_running = False
        for task in self.tasks:
            task.cancel()
        await self.client.close()  # 关闭WebSocket连接
        logger.info("数据采集器已停止")
        
    async def _collect_klines(self, symbol: str):
        """采集K线数据"""
        intervals = ['1m', '5m', '15m', '1h', '4h', '1d']
        session = Session()
        
        try:
            while self.is_running:
                for interval in intervals:
                    try:
                        # 使用WebSocket API获取K线数据
                        klines = await self.client._send_request(
                            method="klines",
                            params={
                                "symbol": symbol,
                                "interval": interval,
                                "limit": 100
                            }
                        )
                        
                        # 保存到数据库
                        for k in klines:
                            kline = Kline(
                                symbol=symbol,
                                interval=interval,
                                open_time=datetime.fromtimestamp(k[0] / 1000),
                                open=float(k[1]),
                                high=float(k[2]),
                                low=float(k[3]),
                                close=float(k[4]),
                                volume=float(k[5]),
                                close_time=datetime.fromtimestamp(k[6] / 1000),
                                quote_volume=float(k[7]),
                                trades_count=int(k[8])
                            )
                            session.merge(kline)
                            
                        session.commit()
                        logger.debug(f"已更新 {symbol} {interval} K线数据")
                        
                    except Exception as e:
                        logger.error(f"采集 {symbol} {interval} K线数据失败: {str(e)}")
                        session.rollback()
                        
                    # 不同间隔的采集频率不同
                    if interval == '1m':
                        await asyncio.sleep(60)  # 1分钟
                    elif interval == '5m':
                        await asyncio.sleep(300)  # 5分钟
                    elif interval == '15m':
                        await asyncio.sleep(900)  # 15分钟
                    else:
                        await asyncio.sleep(3600)  # 1小时
                        
        except asyncio.CancelledError:
            logger.info(f"停止采集 {symbol} K线数据")
        finally:
            session.close()
            
    async def _collect_market_data(self):
        """采集市场数据"""
        session = Session()
        
        try:
            while self.is_running:
                for symbol in self.symbols:
                    try:
                        # 使用WebSocket API获取24小时价格统计
                        ticker = await self.client._send_request(
                            method="ticker.24hr",
                            params={"symbol": symbol}
                        )
                        
                        # 保存到数据库
                        market_data = MarketData(
                            symbol=symbol,
                            price=float(ticker['lastPrice']),
                            volume_24h=float(ticker['volume']),
                            price_change_24h=float(ticker['priceChange']),
                            price_change_percent_24h=float(ticker['priceChangePercent']),
                            high_24h=float(ticker['highPrice']),
                            low_24h=float(ticker['lowPrice'])
                        )
                        session.add(market_data)
                        session.commit()
                        
                        logger.debug(f"已更新 {symbol} 市场数据")
                        
                    except Exception as e:
                        logger.error(f"采集 {symbol} 市场数据失败: {str(e)}")
                        session.rollback()
                        
                await asyncio.sleep(60)  # 每分钟更新一次
                
        except asyncio.CancelledError:
            logger.info("停止采集市场数据")
        finally:
            session.close()
            
    async def backfill_klines(self, 
                             symbol: str,
                             interval: str,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None):
        """补充历史K线数据"""
        session = Session()
        
        try:
            await self.client.connect()  # 确保WebSocket连接已建立
            
            # 默认补充最近7天的数据
            if not start_time:
                start_time = datetime.now() - timedelta(days=7)
            if not end_time:
                end_time = datetime.now()
                
            # 转换为毫秒时间戳
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            # 分批获取数据
            current_start = start_ms
            while current_start < end_ms:
                try:
                    klines = await self.client._send_request(
                        method="klines",
                        params={
                            "symbol": symbol,
                            "interval": interval,
                            "startTime": current_start,
                            "limit": 1000
                        }
                    )
                    
                    if not klines:
                        break
                        
                    # 保存到数据库
                    for k in klines:
                        kline = Kline(
                            symbol=symbol,
                            interval=interval,
                            open_time=datetime.fromtimestamp(k[0] / 1000),
                            open=float(k[1]),
                            high=float(k[2]),
                            low=float(k[3]),
                            close=float(k[4]),
                            volume=float(k[5]),
                            close_time=datetime.fromtimestamp(k[6] / 1000),
                            quote_volume=float(k[7]),
                            trades_count=int(k[8])
                        )
                        session.merge(kline)
                        
                    session.commit()
                    logger.info(f"已补充 {symbol} {interval} K线数据 "
                              f"从 {datetime.fromtimestamp(current_start/1000)}")
                    
                    # 更新开始时间
                    current_start = klines[-1][6] + 1  # 使用上一批数据的结束时间
                    
                except Exception as e:
                    logger.error(f"补充 {symbol} {interval} K线数据失败: {str(e)}")
                    session.rollback()
                    raise
                    
                # 避免触发频率限制
                await asyncio.sleep(1)
                
        finally:
            session.close()
            await self.client.close()  # 关闭WebSocket连接 