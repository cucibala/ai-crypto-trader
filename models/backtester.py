import logging
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class Backtester:
    """
    交易策略回测系统
    """
    
    def __init__(self, 
                 initial_capital: float,
                 trading_fee: float = 0.001,  # 0.1% 交易费用
                 slippage: float = 0.001):    # 0.1% 滑点
        """
        初始化回测系统
        
        Args:
            initial_capital: 初始资金
            trading_fee: 交易费率
            slippage: 滑点率
        """
        self.initial_capital = initial_capital
        self.trading_fee = trading_fee
        self.slippage = slippage
        self.reset()
        
    def reset(self):
        """
        重置回测状态
        """
        self.capital = self.initial_capital  # 当前资金
        self.position = 0  # 当前持仓数量
        self.trades = []  # 交易记录
        self.equity_curve = []  # 资金曲线
        
    async def run_backtest(self,
                          historical_data: List[Dict[str, Any]],
                          strategy: Any,
                          start_time: datetime = None,
                          end_time: datetime = None) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            historical_data: 历史数据
            strategy: 交易策略对象
            start_time: 回测起始时间
            end_time: 回测结束时间
            
        Returns:
            Dict: 回测结果
        """
        try:
            self.reset()
            
            # 转换为DataFrame便于处理
            df = pd.DataFrame(historical_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 时间过滤
            if start_time:
                df = df[df['timestamp'] >= start_time]
            if end_time:
                df = df[df['timestamp'] <= end_time]
                
            # 按时间排序
            df = df.sort_values('timestamp')
            
            # 记录初始资金
            self.equity_curve.append({
                'timestamp': df.iloc[0]['timestamp'],
                'equity': self.capital,
                'position': 0
            })
            
            # 遍历每个时间点
            for i in range(len(df)):
                current_data = df.iloc[i].to_dict()
                
                # 获取策略信号
                signal = await strategy.analyze_market({
                    'historical_data': df.iloc[:i+1].to_dict('records'),
                    'current_data': current_data
                })
                
                # 执行交易
                if signal.get('action') in ['buy', 'sell']:
                    self._execute_trade(
                        timestamp=current_data['timestamp'],
                        price=current_data['price'],
                        action=signal['action'],
                        quantity=signal.get('quantity', 0),
                        reason=signal.get('reasoning', '')
                    )
                    
                # 更新资金曲线
                self.equity_curve.append({
                    'timestamp': current_data['timestamp'],
                    'equity': self._calculate_current_equity(current_data['price']),
                    'position': self.position
                })
                
            # 计算回测结果
            results = self._calculate_backtest_results()
            
            return results
            
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
            
    def _execute_trade(self,
                      timestamp: datetime,
                      price: float,
                      action: str,
                      quantity: float,
                      reason: str = ''):
        """
        执行交易
        """
        # 计算实际成交价格（考虑滑点）
        executed_price = price * (1 + self.slippage) if action == 'buy' else price * (1 - self.slippage)
        
        # 计算交易费用
        fee = executed_price * quantity * self.trading_fee
        
        # 更新资金和持仓
        if action == 'buy':
            cost = executed_price * quantity + fee
            if cost <= self.capital:
                self.capital -= cost
                self.position += quantity
                trade_type = 'buy'
            else:
                logger.warning(f"资金不足，无法执行买入操作")
                return
        else:  # sell
            if quantity <= self.position:
                revenue = executed_price * quantity - fee
                self.capital += revenue
                self.position -= quantity
                trade_type = 'sell'
            else:
                logger.warning(f"持仓不足，无法执行卖出操作")
                return
                
        # 记录交易
        self.trades.append({
            'timestamp': timestamp,
            'type': trade_type,
            'price': executed_price,
            'quantity': quantity,
            'fee': fee,
            'reason': reason
        })
        
    def _calculate_current_equity(self, current_price: float) -> float:
        """
        计算当前权益
        """
        return self.capital + self.position * current_price
        
    def _calculate_backtest_results(self) -> Dict[str, Any]:
        """
        计算回测结果统计
        """
        if not self.equity_curve:
            return {
                'status': 'failed',
                'error': '没有交易数据'
            }
            
        # 转换为DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        
        # 计算收益率
        initial_equity = self.initial_capital
        final_equity = equity_df.iloc[-1]['equity']
        total_return = (final_equity - initial_equity) / initial_equity
        
        # 计算最大回撤
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['cummax'] - equity_df['equity']) / equity_df['cummax']
        max_drawdown = equity_df['drawdown'].max()
        
        # 计算交易统计
        if not trades_df.empty:
            winning_trades = trades_df[trades_df['type'] == 'sell']['price'].gt(
                trades_df[trades_df['type'] == 'buy']['price'].values
            ).sum()
            total_trades = len(trades_df[trades_df['type'] == 'sell'])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # 计算收益率统计
            returns = equity_df['equity'].pct_change().dropna()
            sharpe_ratio = np.sqrt(252) * (returns.mean() / returns.std()) if len(returns) > 0 else 0
        else:
            winning_trades = 0
            total_trades = 0
            win_rate = 0
            sharpe_ratio = 0
            
        return {
            'status': 'success',
            'initial_capital': initial_equity,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'trade_statistics': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': win_rate,
                'win_rate_pct': win_rate * 100
            },
            'risk_metrics': {
                'sharpe_ratio': sharpe_ratio,
                'volatility': returns.std() * np.sqrt(252) if 'returns' in locals() else 0
            },
            'equity_curve': self.equity_curve,
            'trades': self.trades
        } 