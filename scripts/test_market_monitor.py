#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
import logging
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.analyzer.market_analyzer import MarketAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_market_monitor():
    """测试市场监控功能"""
    try:
        # 创建市场监控器
        symbols = ['DOGEUSDT']
        analyzer = MarketAnalyzer(symbols)
        
        # 1. 获取市场摘要
        logger.info("1. 获取市场摘要...")
        summary = await analyzer.get_market_summary('DOGEUSDT')
        if summary:
            logger.info("市场摘要:")
            logger.info(json.dumps(summary, indent=2))
        
        # 2. 启动市场监控
        logger.info("\n2. 启动市场监控...")
        await analyzer.start()
        
        # 运行10分钟
        logger.info("市场监控中，将运行10分钟...")
        await asyncio.sleep(600)
        
        # 停止监控
        await monitor.stop()
        logger.info("市场监控已停止")
        
    except Exception as e:
        logger.error("测试失败: %s", str(e))
        raise

async def main():
    """主函数"""
    try:
        await test_market_monitor()
        logger.info("\n测试完成 ✅")
        
    except KeyboardInterrupt:
        logger.info("程序终止")
    except Exception as e:
        logger.error("程序错误: %s", str(e))
        raise

if __name__ == '__main__':
    asyncio.run(main()) 