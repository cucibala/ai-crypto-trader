#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from models.strategies.simple_ma_strategy import SimpleMAStrategy
from models.backtest_runner import BacktestRunner

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """主函数"""
    try:
        # 创建回测运行器
        runner = BacktestRunner(
            strategy_class=SimpleMAStrategy,
            symbol="BTCUSDT",
            timeframe="1h",
            initial_capital=10000.0,
            commission_rate=0.001
        )
        
        # 设置回测时间范围（最近30天）
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        # 设置策略参数
        strategy_params = {
            'short_window': 10,
            'long_window': 30,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30
        }
        
        # 运行回测
        logging.info("开始回测...")
        results = await runner.run(start_time, end_time, strategy_params)
        
        # 打印回测结果
        logging.info("\n回测结果摘要:")
        logging.info("=" * 50)
        logging.info(f"总交易次数: {results.total_trades}")
        logging.info(f"盈利交易: {results.winning_trades}")
        logging.info(f"亏损交易: {results.losing_trades}")
        logging.info(f"胜率: {results.win_rate:.2%}")
        logging.info(f"总收益: {results.total_pnl:.2f} USDT")
        logging.info(f"最大回撤: {results.max_drawdown:.2%}")
        logging.info(f"夏普比率: {results.sharpe_ratio:.2f}")
        
        # 打印详细指标
        logging.info("\n详细指标:")
        logging.info("=" * 50)
        for metric, value in results.metrics.items():
            if isinstance(value, float):
                logging.info(f"{metric}: {value:.4f}")
            else:
                logging.info(f"{metric}: {value}")
                
        # 参数优化（可选）
        optimize = input("\n是否进行参数优化？(y/n): ").lower().strip() == 'y'
        if optimize:
            logging.info("\n开始参数优化...")
            
            # 定义参数网格
            param_grid = {
                'short_window': [5, 10, 15, 20],
                'long_window': [20, 30, 40, 50],
                'rsi_period': [7, 14, 21],
                'rsi_overbought': [65, 70, 75],
                'rsi_oversold': [25, 30, 35]
            }
            
            # 运行优化
            best_params = await runner.optimize_parameters(
                param_grid=param_grid,
                start_time=start_time,
                end_time=end_time
            )
            
            logging.info(f"\n最优参数组合: {best_params}")
            
    except Exception as e:
        logging.error(f"回测执行失败: {str(e)}")
        raise

if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main()) 