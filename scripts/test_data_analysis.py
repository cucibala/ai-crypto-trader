#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
import logging
from datetime import datetime, timedelta
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.collector.data_collector import DataCollector
from services.analyzer.data_analyzer import DataAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_data_collection():
    """测试数据采集"""
    try:
        # 创建数据采集器
        collector = DataCollector(['DOGEUSDT'])
        
        # 1. 补充历史数据
        logger.info("1. 开始补充历史数据...")
        await collector.backfill_klines(
            symbol='DOGEUSDT',
            interval='1h',
            start_time=datetime.now() - timedelta(days=7)
        )
        
        # 2. 启动实时数据采集
        logger.info("\n2. 启动实时数据采集...")
        await collector.start()
        
        # 运行5分钟
        logger.info("数据采集中，将运行5分钟...")
        await asyncio.sleep(300)
        
        # 停止采集
        await collector.stop()
        logger.info("数据采集已停止")
        
    except Exception as e:
        logger.error("数据采集测试失败: %s", str(e))
        raise

def test_data_analysis():
    """测试数据分析"""
    try:
        # 创建数据分析器
        analyzer = DataAnalyzer()
        symbol = 'DOGEUSDT'
        
        # 1. 分析市场趋势
        logger.info("1. 分析市场趋势...")
        trend = analyzer.analyze_market_trend(symbol)
        logger.info("市场趋势分析结果:")
        logger.info(json.dumps(trend, indent=2))
        
        # 2. 分析交易表现
        logger.info("\n2. 分析交易表现...")
        performance = analyzer.analyze_trading_performance(symbol)
        logger.info("交易表现分析结果:")
        logger.info(json.dumps(performance, indent=2))
        
        # 3. 计算技术指标
        logger.info("\n3. 计算技术指标...")
        indicators = analyzer.calculate_indicators(symbol)
        logger.info("技术指标计算结果:")
        logger.info(json.dumps(indicators, indent=2))
        
        # 4. 生成汇总报告
        logger.info("\n4. 生成汇总报告...")
        report = analyzer.get_summary_report(symbol)
        logger.info("汇总报告:")
        logger.info(json.dumps(report, indent=2))
        
    except Exception as e:
        logger.error("数据分析测试失败: %s", str(e))
        raise

async def main():
    """主函数"""
    try:
        # 1. 测试数据采集
        logger.info("开始测试数据采集功能...")
        await test_data_collection()
        
        # 2. 测试数据分析
        logger.info("\n开始测试数据分析功能...")
        test_data_analysis()
        
        logger.info("\n测试完成 ✅")
        
    except KeyboardInterrupt:
        logger.info("程序终止")
    except Exception as e:
        logger.error("测试失败: %s", str(e))
        raise

if __name__ == '__main__':
    asyncio.run(main()) 