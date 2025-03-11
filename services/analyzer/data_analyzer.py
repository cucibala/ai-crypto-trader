import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sqlalchemy import func, and_

from models.database import Session, Kline, Trade, MarketData

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self):
        """初始化数据分析器"""
        self.session = Session()
        
    def analyze_market_trend(self, symbol: str, days: int = 7) -> Dict:
        """分析市场趋势
        
        Args:
            symbol: 交易对
            days: 分析天数
            
        Returns:
            Dict: 趋势分析结果
        """
        try:
            # 获取指定时间范围的市场数据
            start_time = datetime.now() - timedelta(days=days)
            market_data = self.session.query(MarketData).filter(
                and_(
                    MarketData.symbol == symbol,
                    MarketData.created_at >= start_time
                )
            ).all()
            
            if not market_data:
                return {}
                
            # 转换为DataFrame
            df = pd.DataFrame([{
                'timestamp': data.created_at,
                'price': data.price,
                'volume': data.volume_24h,
                'price_change': data.price_change_24h,
                'price_change_percent': data.price_change_percent_24h
            } for data in market_data])
            
            # 计算基本统计数据
            stats = {
                'current_price': float(df['price'].iloc[-1]),
                'price_change_7d': float(df['price'].iloc[-1] - df['price'].iloc[0]),
                'price_change_percent_7d': float((df['price'].iloc[-1] / df['price'].iloc[0] - 1) * 100),
                'avg_price': float(df['price'].mean()),
                'max_price': float(df['price'].max()),
                'min_price': float(df['price'].min()),
                'volatility': float(df['price'].std()),
                'avg_volume': float(df['volume'].mean()),
                'trend': 'up' if df['price'].iloc[-1] > df['price'].iloc[0] else 'down'
            }
            
            # 计算移动平均线
            df['MA5'] = df['price'].rolling(window=5).mean()
            df['MA10'] = df['price'].rolling(window=10).mean()
            df['MA20'] = df['price'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            stats.update({
                'MA5': float(latest['MA5']) if not pd.isna(latest['MA5']) else None,
                'MA10': float(latest['MA10']) if not pd.isna(latest['MA10']) else None,
                'MA20': float(latest['MA20']) if not pd.isna(latest['MA20']) else None
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"分析市场趋势失败: {str(e)}")
            return {}
            
    def analyze_trading_performance(self, symbol: str, days: int = 30) -> Dict:
        """分析交易表现
        
        Args:
            symbol: 交易对
            days: 分析天数
            
        Returns:
            Dict: 交易分析结果
        """
        try:
            # 获取指定时间范围的交易记录
            start_time = datetime.now() - timedelta(days=days)
            trades = self.session.query(Trade).filter(
                and_(
                    Trade.symbol == symbol,
                    Trade.created_at >= start_time,
                    Trade.status == 'FILLED'
                )
            ).all()
            
            if not trades:
                return {}
                
            # 转换为DataFrame
            df = pd.DataFrame([{
                'timestamp': trade.created_at,
                'side': trade.side,
                'quantity': trade.quantity,
                'price': trade.price,
                'executed_price': trade.executed_price,
                'fee': trade.fee
            } for trade in trades])
            
            # 计算交易统计
            buy_trades = df[df['side'] == 'BUY']
            sell_trades = df[df['side'] == 'SELL']
            
            stats = {
                'total_trades': len(trades),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades),
                'avg_trade_size': float(df['quantity'].mean()),
                'total_volume': float(df['quantity'].sum()),
                'avg_price': float(df['executed_price'].mean()),
                'total_fee': float(df['fee'].sum())
            }
            
            # 计算盈亏
            if not sell_trades.empty and not buy_trades.empty:
                avg_buy_price = float(buy_trades['executed_price'].mean())
                avg_sell_price = float(sell_trades['executed_price'].mean())
                stats.update({
                    'avg_buy_price': avg_buy_price,
                    'avg_sell_price': avg_sell_price,
                    'profit_loss': float((avg_sell_price - avg_buy_price) * df['quantity'].mean())
                })
                
            return stats
            
        except Exception as e:
            logger.error(f"分析交易表现失败: {str(e)}")
            return {}
            
    def calculate_indicators(self, symbol: str, interval: str = '1h', limit: int = 100) -> Dict:
        """计算技术指标
        
        Args:
            symbol: 交易对
            interval: K线间隔
            limit: 数据点数量
            
        Returns:
            Dict: 技术指标值
        """
        try:
            # 获取K线数据
            klines = self.session.query(Kline).filter(
                and_(
                    Kline.symbol == symbol,
                    Kline.interval == interval
                )
            ).order_by(Kline.open_time.desc()).limit(limit).all()
            
            if not klines:
                return {}
                
            # 转换为DataFrame
            df = pd.DataFrame([{
                'timestamp': kline.open_time,
                'open': kline.open,
                'high': kline.high,
                'low': kline.low,
                'close': kline.close,
                'volume': kline.volume
            } for kline in klines]).sort_values('timestamp')
            
            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 计算MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # 计算布林带
            ma20 = df['close'].rolling(window=20).mean()
            std20 = df['close'].rolling(window=20).std()
            upper_band = ma20 + (std20 * 2)
            lower_band = ma20 - (std20 * 2)
            
            latest = df.iloc[-1]
            indicators = {
                'RSI': float(rsi.iloc[-1]),
                'MACD': float(macd.iloc[-1]),
                'MACD_Signal': float(signal.iloc[-1]),
                'MACD_Histogram': float(macd.iloc[-1] - signal.iloc[-1]),
                'BB_Middle': float(ma20.iloc[-1]),
                'BB_Upper': float(upper_band.iloc[-1]),
                'BB_Lower': float(lower_band.iloc[-1])
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            return {}
            
    def get_summary_report(self, symbol: str) -> Dict:
        """生成汇总报告
        
        Args:
            symbol: 交易对
            
        Returns:
            Dict: 汇总报告
        """
        try:
            # 获取市场趋势分析
            market_trend = self.analyze_market_trend(symbol)
            
            # 获取交易表现分析
            trading_performance = self.analyze_trading_performance(symbol)
            
            # 获取技术指标
            indicators = self.calculate_indicators(symbol)
            
            # 汇总报告
            report = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'market_trend': market_trend,
                'trading_performance': trading_performance,
                'technical_indicators': indicators
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成汇总报告失败: {str(e)}")
            return {} 