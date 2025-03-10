#!/usr/bin/env python3
import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import API_KEYS, MODEL_CONFIG, _get_env_var
from models.sentiment_analyzer import SentimentAnalyzer

async def fetch_crypto_news(session, symbol="BTC"):
    """
    获取加密货币相关新闻
    
    Args:
        session: aiohttp会话
        symbol: 加密货币符号
    """
    try:
        # 从配置中获取API密钥
        news_api_key = API_KEYS.get('news')
        if not news_api_key:
            raise ValueError("未配置 NEWS_API_KEY，请在 .env 文件中设置 NEWS_API_KEY")

        # 构建查询参数
        params = {
            'q': f'cryptocurrency {symbol} OR bitcoin OR crypto',
            'apiKey': news_api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 20,  # 获取更多新闻以提高分析准确性
            'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        }

        print("正在获取新闻...")
        
        # 发送请求
        async with session.get(
            'https://newsapi.org/v2/everything',
            params=params
        ) as response:
            if response.status != 200:
                error_data = await response.text()
                print(f"API请求失败: 状态码 {response.status}")
                print(f"错误详情: {error_data}")
                return []
                
            data = await response.json()
            
            if 'articles' not in data:
                print(f"API响应格式错误: {data}")
                return []
                
            articles = data['articles']
            print(f"成功获取 {len(articles)} 条新闻")
            
            # 处理新闻数据
            processed_news = []
            for article in articles:
                if not article.get('title'):  # 跳过没有标题的文章
                    continue
                processed_news.append({
                    'title': article.get('title', ''),
                    'summary': article.get('description', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'url': article.get('url', ''),
                    'timestamp': article.get('publishedAt', ''),
                })
                
            return processed_news
            
    except ValueError as ve:
        print(f"配置错误: {str(ve)}")
        return []
    except aiohttp.ClientError as ce:
        print(f"网络请求错误: {str(ce)}")
        return []
    except Exception as e:
        print(f"获取新闻失败: {str(e)}")
        print(f"错误类型: {type(e)}")
        return []

def print_news_details(news_list):
    """打印新闻详情"""
    print(f"\n获取到 {len(news_list)} 条新闻")
    
    if not news_list:
        return
        
    print("\n最新新闻摘要:")
    for i, news in enumerate(news_list[:5], 1):  # 只显示前5条
        print(f"\n{i}. {news['title']}")
        print(f"   来源: {news['source']}")
        print(f"   时间: {news['timestamp']}")
        print(f"   链接: {news['url']}")

def print_sentiment_analysis(sentiment_result):
    """打印情绪分析结果"""
    print("\n情绪分析结果:")
    print("=" * 50)
    
    # 打印整体情绪
    sentiment_map = {
        'bullish': '看涨 📈',
        'bearish': '看跌 📉',
        'neutral': '中性 ↔️'
    }
    overall = sentiment_result.get('overall', 'neutral')
    print(f"整体情绪: {sentiment_map.get(overall, overall)}")
    
    # 打印置信度
    confidence = sentiment_result.get('confidence', 0)
    confidence_bar = '█' * int(confidence * 20)
    print(f"置信度: {confidence:.2%} [{confidence_bar:<20}]")
    
    # 打印关键影响因素
    if 'key_factors' in sentiment_result:
        print("\n关键影响因素:")
        for factor in sentiment_result['key_factors']:
            print(f"• {factor}")
    
    # 打印市场影响
    if 'potential_impact' in sentiment_result:
        print("\n潜在市场影响:")
        print(sentiment_result['potential_impact'])
    
    # 打印分析理由
    if 'reasoning' in sentiment_result:
        print("\n分析理由:")
        print(sentiment_result['reasoning'])
    
    print("=" * 50)

async def main():
    """主函数"""
    # 创建分析器实例
    analyzer = SentimentAnalyzer()
    
    # 从配置文件中获取代理设置
    http_proxy = _get_env_var('HTTP_PROXY', required=False)
    https_proxy = _get_env_var('HTTPS_PROXY', required=False)
    
    if http_proxy or https_proxy:
        print(f"使用代理: HTTP={http_proxy}, HTTPS={https_proxy}")
        # 设置环境变量以供 aiohttp 使用
        if http_proxy:
            os.environ['HTTP_PROXY'] = http_proxy
        if https_proxy:
            os.environ['HTTPS_PROXY'] = https_proxy
        async with aiohttp.ClientSession(trust_env=True) as session:
            await run_analysis(session, analyzer)
    else:
        print("未配置代理，使用直接连接")
        async with aiohttp.ClientSession() as session:
            await run_analysis(session, analyzer)

async def run_analysis(session, analyzer):
    """运行分析流程"""
    # 获取新闻
    news_list = await fetch_crypto_news(session)
    
    if not news_list:
        print("未获取到新闻数据")
        return
        
    # 打印新闻详情
    print_news_details(news_list)
    
    # 进行情绪分析
    sentiment_result = await analyzer._analyze_news_sentiment(news_list)
    
    # 打印分析结果
    print_sentiment_analysis(sentiment_result)
    
    # 保存结果到文件
    result = {
        'timestamp': datetime.now().isoformat(),
        'news_count': len(news_list),
        'sentiment_analysis': sentiment_result
    }
    
    # 确保results目录存在
    results_dir = project_root / 'results'
    results_dir.mkdir(exist_ok=True)
    
    # 保存结果
    result_file = results_dir / f'news_sentiment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    print(f"\n分析结果已保存到: {result_file}")

if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main()) 