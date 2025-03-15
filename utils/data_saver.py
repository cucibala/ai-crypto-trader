import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from models.database import Kline, MarketAnalysis

logger = logging.getLogger(__name__)

class DataSaver:
    """数据保存工具类"""
    
    def __init__(self, db_session: Session):
        """初始化数据保存器
        
        Args:
            db_session: SQLAlchemy数据库会话
        """
        self.db = db_session
        
    def save_klines(self, klines_data: List[List], symbol: str, interval: str) -> None:
        """保存K线数据
        
        Args:
            klines_data: K线数据列表
            symbol: 交易对符号
            interval: K线时间间隔 (1h, 4h, 1d等)
        """
        try:
            for kline in klines_data:
                # 检查是否已存在相同的K线数据
                existing_kline = self.db.query(Kline).filter_by(
                    symbol=symbol,
                    interval=interval,
                    open_time=datetime.fromtimestamp(kline[0] / 1000)  # 将毫秒时间戳转换为datetime
                ).first()
                
                if not existing_kline:
                    kline_record = Kline(
                        symbol=symbol,
                        interval=interval,
                        open_time=datetime.fromtimestamp(kline[0] / 1000),
                        open_price=float(kline[1]),
                        high_price=float(kline[2]),
                        low_price=float(kline[3]),
                        close_price=float(kline[4]),
                        volume=float(kline[5]),
                        close_time=datetime.fromtimestamp(kline[6] / 1000),
                        quote_volume=float(kline[7]),
                        trades_count=int(kline[8]),
                        taker_buy_volume=float(kline[9]),
                        taker_buy_quote_volume=float(kline[10])
                    )
                    self.db.add(kline_record)
                    
            self.db.commit()
            logger.debug(f"已保存 {symbol} {interval} K线数据 {len(klines_data)} 条")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存K线数据失败: {str(e)}")
            raise
            
    def save_market_analysis(self,
                           symbol: str,
                           price: float,
                           price_change_24h: float,
                           volume_24h: float,
                           quote_volume: float,
                           volume_change_24h: float,
                           volume_vs_7d_avg: float,
                           rsi_data: Dict[str, float],
                           macd_data: Dict[str, Dict[str, float]],
                           bollinger_data: Dict[str, float],
                           price_trends: Dict[str, Any],
                           analysis_result: Dict[str, Any],
                           strategy: Dict[str, Any],
                           request_ip: str,
                           request_timestamp: datetime,
                           response_time: float) -> Optional[MarketAnalysis]:
        """保存市场分析数据
        
        Args:
            symbol: 交易对符号
            price: 当前价格
            price_change_24h: 24小时价格变化百分比
            volume_24h: 24小时成交量
            quote_volume: 24小时计价货币成交量
            volume_change_24h: 24小时成交量变化百分比
            volume_vs_7d_avg: 相对7日均量百分比
            rsi_data: RSI指标数据
            macd_data: MACD指标数据
            bollinger_data: 布林带位置数据
            price_trends: 价格趋势数据
            analysis_result: AI分析结果
            strategy: 交易策略建议
            request_ip: 请求IP
            request_timestamp: 请求时间戳
            response_time: 响应时间(毫秒)
            
        Returns:
            MarketAnalysis: 保存的市场分析记录
        """
        try:
            market_analysis = MarketAnalysis(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                price=price,
                price_change_24h=price_change_24h,
                volume_24h=volume_24h,
                quote_volume=quote_volume,
                volume_change_24h=volume_change_24h,
                volume_vs_7d_avg=volume_vs_7d_avg,
                rsi_data=rsi_data,
                macd_data=macd_data,
                bollinger_data=bollinger_data,
                price_trends=price_trends,
                analysis_result=analysis_result,
                strategy=strategy,
                request_ip=request_ip,
                request_timestamp=request_timestamp,
                response_time=response_time
            )
            
            self.db.add(market_analysis)
            self.db.commit()
            
            logger.info(f"市场分析数据已保存到数据库，ID: {market_analysis.id}")
            return market_analysis
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存市场分析数据失败: {str(e)}")
            raise
            
    def save_all_klines(self, 
                       klines_1d: List[List],
                       klines_4h: List[List],
                       klines_1h: List[List],
                       symbol: str) -> None:
        """批量保存多个时间维度的K线数据
        
        Args:
            klines_1d: 日线数据
            klines_4h: 4小时线数据
            klines_1h: 1小时线数据
            symbol: 交易对符号
        """
        try:
            self.save_klines(klines_1d, symbol, '1d')
            self.save_klines(klines_4h, symbol, '4h')
            self.save_klines(klines_1h, symbol, '1h')
            logger.info(f"已保存所有时间维度的K线数据")
            
        except Exception as e:
            logger.error(f"批量保存K线数据失败: {str(e)}")
            raise 