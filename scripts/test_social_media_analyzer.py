#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
import logging
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.analyzer.social_media_analyzer import SocialMediaAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_social_media_analysis():
    """测试社交媒体分析功能"""
    try:
        analyzer = SocialMediaAnalyzer()
        symbol = 'BTC'
        lookback_hours = 24
        
        # 1. 测试Twitter情绪分析
        logger.info("\n1. 测试Twitter情绪分析...")
        twitter_sentiment = await analyzer.analyze_twitter_sentiment(symbol, lookback_hours)
        logger.info(f"Twitter情绪分析结果: {twitter_sentiment}")
        
        # 2. 测试Reddit情绪分析
        logger.info("\n2. 测试Reddit情绪分析...")
        reddit_sentiment = await analyzer.analyze_reddit_sentiment(symbol, lookback_hours)
        logger.info(f"Reddit情绪分析结果: {reddit_sentiment}")
        
        # 3. 测试Telegram情绪分析
        logger.info("\n3. 测试Telegram情绪分析...")
        telegram_sentiment = await analyzer.analyze_telegram_sentiment(symbol, lookback_hours)
        logger.info(f"Telegram情绪分析结果: {telegram_sentiment}")
        
        # 4. 测试聚合情绪分析
        logger.info("\n4. 测试聚合情绪分析...")
        aggregated_sentiment = await analyzer.get_aggregated_sentiment(symbol, lookback_hours)
        logger.info(f"聚合情绪分析结果: {aggregated_sentiment}")
        
        logger.info("\n测试完成 ✅")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise

async def main():
    """主函数"""
    try:
        await test_social_media_analysis()
    except KeyboardInterrupt:
        logger.info("程序终止")
    except Exception as e:
        logger.error(f"程序错误: {str(e)}")
        raise

if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main()) 