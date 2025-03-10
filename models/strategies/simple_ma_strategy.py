import logging
from typing import Dict, List, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class SimpleMAStrategy:
    """
    简单移动平均线策略
    
    策略逻辑：
    1. 当短期MA上穿长期MA时买入
    2. 当短期MA下穿长期MA时卖出
    3. 使用RSI作为过滤器，避免过度交易
    """
    
    def __init__(self,
                 short_window: int = 5,
                 long_window: int = 20,
                 rsi_period: int = 14,
                 rsi_overbought: int = 70,
                 rsi_oversold: int = 30,
                 position_size: float = 0.1):  # 默认使用10%资金
        """
        初始化策略参数
        
        Args:
            short_window: 短期MA窗口
            long_window: 长期MA窗口
            rsi_period: RSI计算周期
            rsi_overbought: RSI超买阈值
            rsi_oversold: RSI超卖阈值
            position_size: 每次交易使用的资金比例
        """
        self.short_window = short_window
        self.long_window = long_window
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.position_size = position_size
        
    async def analyze_market(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场数据并生成交易信号
        
        Args:
            data: 包含历史数据和当前数据的字典
            
        Returns:
            Dict: 交易信号
        """
        try:
            # 获取历史数据
            historical_data = data['historical_data']
            current_data = data['current_data']
            
            # 转换为DataFrame
            df = pd.DataFrame(historical_data)
            
            # 计算技术指标
            df['SMA_short'] = df['price'].rolling(window=self.short_window).mean()
            df['SMA_long'] = df['price'].rolling(window=self.long_window).mean()
            df['RSI'] = self._calculate_rsi(df['price'], self.rsi_period)
            
            # 如果数据不足，返回不交易信号
            if len(df) < self.long_window:
                return {
                    'action': 'hold',
                    'reason': '数据不足'
                }
                
            # 获取当前和前一个时间点的指标值
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # 生成交易信号
            signal = self._generate_signal(current, previous)
            
            # 如果有交易信号，计算交易数量
            if signal['action'] in ['buy', 'sell']:
                price = current_data['price']
                available_capital = data.get('available_capital', 10000)  # 默认资金
                signal['quantity'] = self._calculate_position_size(price, available_capital)
                
            return signal
            
        except Exception as e:
            logger.error(f"策略分析失败: {e}")
            return {
                'action': 'hold',
                'reason': f'策略分析错误: {str(e)}'
            }
            
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        计算RSI指标
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def _generate_signal(self, current: pd.Series, previous: pd.Series) -> Dict[str, Any]:
        """
        生成交易信号
        """
        # 检查是否发生均线交叉
        previous_cross = previous['SMA_short'] - previous['SMA_long']
        current_cross = current['SMA_short'] - current['SMA_long']
        
        # 买入条件：短期均线上穿长期均线，且RSI处于超卖区域
        if previous_cross < 0 and current_cross > 0 and current['RSI'] < self.rsi_oversold:
            return {
                'action': 'buy',
                'reasoning': f'均线金叉，RSI={current["RSI"]:.2f}处于超卖区域'
            }
            
        # 卖出条件：短期均线下穿长期均线，且RSI处于超买区域
        elif previous_cross > 0 and current_cross < 0 and current['RSI'] > self.rsi_overbought:
            return {
                'action': 'sell',
                'reasoning': f'均线死叉，RSI={current["RSI"]:.2f}处于超买区域'
            }
            
        # 其他情况保持不变
        return {
            'action': 'hold',
            'reasoning': '没有交易信号'
        }
        
    def _calculate_position_size(self, price: float, available_capital: float) -> float:
        """
        计算交易数量
        """
        position_value = available_capital * self.position_size
        quantity = position_value / price
        return quantity
        
    async def optimize_parameters(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        优化策略参数
        """
        try:
            # 转换为DataFrame
            df = pd.DataFrame(historical_data)
            
            # 定义参数网格
            short_windows = range(3, 15, 2)
            long_windows = range(10, 50, 5)
            rsi_periods = range(10, 30, 2)
            
            best_params = None
            best_sharpe = -np.inf
            
            # 网格搜索最优参数
            for short_window in short_windows:
                for long_window in long_windows:
                    if short_window >= long_window:
                        continue
                    for rsi_period in rsi_periods:
                        # 计算指标
                        df['SMA_short'] = df['price'].rolling(window=short_window).mean()
                        df['SMA_long'] = df['price'].rolling(window=long_window).mean()
                        df['RSI'] = self._calculate_rsi(df['price'], rsi_period)
                        
                        # 生成交易信号
                        df['position'] = 0
                        for i in range(1, len(df)):
                            signal = self._generate_signal(df.iloc[i], df.iloc[i-1])
                            df.loc[df.index[i], 'position'] = 1 if signal['action'] == 'buy' else (-1 if signal['action'] == 'sell' else 0)
                            
                        # 计算收益
                        df['returns'] = df['price'].pct_change() * df['position'].shift(1)
                        
                        # 计算夏普比率
                        if len(df['returns'].dropna()) > 0:
                            sharpe = np.sqrt(252) * df['returns'].mean() / df['returns'].std()
                            
                            if sharpe > best_sharpe:
                                best_sharpe = sharpe
                                best_params = {
                                    'short_window': short_window,
                                    'long_window': long_window,
                                    'rsi_period': rsi_period
                                }
                                
            return {
                'status': 'success',
                'optimized_parameters': best_params,
                'performance_metric': {
                    'sharpe_ratio': best_sharpe
                }
            }
            
        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            } 