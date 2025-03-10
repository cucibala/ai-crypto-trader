import unittest
import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import MODEL_CONFIG
from models.sentiment_analyzer import SentimentAnalyzer

class TestNewsAPI(unittest.TestCase):
    """测试新闻API功能"""

    def setUp(self):
        """测试前的设置"""
        self.news_api_key = MODEL_CONFIG.get('news_api_key')
        self.session = None
        self.analyzer = SentimentAnalyzer()

    async def asyncSetUp(self):
        """异步设置"""
        self.session = aiohttp.ClientSession()

    async def asyncTearDown(self):
        """异步清理"""
        if self.session:
            await self.session.close()

    async def test_fetch_crypto_news(self):
        """测试获取加密货币新闻"""
        if not self.news_api_key:
            self.skipTest("News API密钥未配置")

        try:
            # 构建查询参数
            params = {
                'q': 'cryptocurrency bitcoin',
                'apiKey': self.news_api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 10,  # 限制数量，用于测试
                'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # 最近24小时的新闻
            }

            # 发送请求
            async with self.session.get(
                'https://newsapi.org/v2/everything',
                params=params
            ) as response:
                self.assertEqual(response.status, 200, "API请求失败")
                data = await response.json()

                # 验证响应格式
                self.assertIn('articles', data, "响应中缺少articles字段")
                self.assertIsInstance(data['articles'], list, "articles不是列表类型")
                
                # 打印获取到的新闻数量
                print(f"\n获取到 {len(data['articles'])} 条新闻")

                # 处理新闻数据
                processed_news = []
                for article in data['articles']:
                    processed_news.append({
                        'title': article.get('title', ''),
                        'summary': article.get('description', ''),
                        'source': article.get('source', {}).get('name', ''),
                        'url': article.get('url', ''),
                        'timestamp': article.get('publishedAt', ''),
                    })

                # 打印第一条新闻的详细信息
                if processed_news:
                    print("\n第一条新闻详情:")
                    print(f"标题: {processed_news[0]['title']}")
                    print(f"摘要: {processed_news[0]['summary']}")
                    print(f"来源: {processed_news[0]['source']}")
                    print(f"时间: {processed_news[0]['timestamp']}")

                # 使用情绪分析器分析新闻情绪
                sentiment_result = await self.analyzer._analyze_news_sentiment(processed_news)
                
                # 验证情绪分析结果
                self.assertIn('overall', sentiment_result, "情绪分析结果缺少overall字段")
                self.assertIn(sentiment_result['overall'], ['bullish', 'bearish', 'neutral'], 
                            "情绪值不在预期范围内")
                
                # 打印情绪分析结果
                print("\n情绪分析结果:")
                print(f"整体情绪: {sentiment_result['overall']}")
                print(f"置信度: {sentiment_result.get('confidence', 0)}")
                if 'key_factors' in sentiment_result:
                    print("\n关键影响因素:")
                    for factor in sentiment_result['key_factors']:
                        print(f"- {factor}")

        except Exception as e:
            self.fail(f"测试失败: {str(e)}")

def async_test(coro):
    """装饰器：运行异步测试"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

if __name__ == '__main__':
    # 设置详细的测试输出
    unittest.main(verbosity=2) 