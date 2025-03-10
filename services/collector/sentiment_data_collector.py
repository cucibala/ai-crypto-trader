import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json

logger = logging.getLogger(__name__)

class SentimentDataCollector:
    """
    情绪数据收集器
    负责从各种来源收集市场情绪相关数据：
    1. Twitter/X（加密货币相关推文）
    2. Reddit（加密货币相关帖子）
    3. 新闻API（加密货币新闻）
    4. Telegram（加密货币群组消息）
    """
    
    def __init__(self,
                 twitter_api_key: str = None,
                 reddit_api_key: str = None,
                 news_api_key: str = None,
                 telegram_api_key: str = None):
        """
        初始化数据收集器
        
        Args:
            twitter_api_key: Twitter API密钥
            reddit_api_key: Reddit API密钥
            news_api_key: 新闻API密钥
            telegram_api_key: Telegram API密钥
        """
        self.twitter_api_key = twitter_api_key
        self.reddit_api_key = reddit_api_key
        self.news_api_key = news_api_key
        self.telegram_api_key = telegram_api_key
        self.session = None
        
    async def initialize(self):
        """
        初始化HTTP会话
        """
        self.session = aiohttp.ClientSession()
        
    async def close(self):
        """
        关闭HTTP会话
        """
        if self.session:
            await self.session.close()
            
    async def collect_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """
        收集所有情绪数据
        
        Args:
            symbol: 交易对符号（例如：BTCUSDT）
            
        Returns:
            Dict: 包含所有情绪数据的字典
        """
        try:
            # 并行收集数据
            social_data_task = asyncio.create_task(self.collect_social_data(symbol))
            news_data_task = asyncio.create_task(self.collect_news_data(symbol))
            
            # 等待所有任务完成
            social_data, news_data = await asyncio.gather(
                social_data_task,
                news_data_task
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "social_data": social_data,
                "news_data": news_data
            }
            
        except Exception as e:
            logger.error(f"情绪数据收集失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def collect_social_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        收集社交媒体数据
        """
        try:
            # 并行收集各平台数据
            twitter_task = asyncio.create_task(self._collect_twitter_data(symbol))
            reddit_task = asyncio.create_task(self._collect_reddit_data(symbol))
            telegram_task = asyncio.create_task(self._collect_telegram_data(symbol))
            
            # 等待所有任务完成
            twitter_data, reddit_data, telegram_data = await asyncio.gather(
                twitter_task,
                reddit_task,
                telegram_task
            )
            
            # 合并所有数据
            all_data = []
            all_data.extend(twitter_data)
            all_data.extend(reddit_data)
            all_data.extend(telegram_data)
            
            # 按时间排序
            all_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return all_data
            
        except Exception as e:
            logger.error(f"社交媒体数据收集失败: {e}")
            return []
            
    async def collect_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        收集新闻数据
        """
        try:
            if not self.news_api_key:
                return []
                
            # 构建查询参数
            coin = symbol.replace('USDT', '').lower()  # 从交易对中提取币种名称
            
            # 使用NewsAPI获取新闻
            async with self.session.get(
                'https://newsapi.org/v2/everything',
                params={
                    'q': f'cryptocurrency {coin}',
                    'apiKey': self.news_api_key,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 100
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get('articles', [])
                    
                    # 处理新闻数据
                    processed_news = []
                    for article in articles:
                        processed_news.append({
                            'title': article.get('title', ''),
                            'summary': article.get('description', ''),
                            'source': article.get('source', {}).get('name', ''),
                            'url': article.get('url', ''),
                            'timestamp': article.get('publishedAt', ''),
                            'sentiment_score': None  # 待后续分析
                        })
                        
                    return processed_news
                else:
                    logger.error(f"新闻API请求失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"新闻数据收集失败: {e}")
            return []
            
    async def _collect_twitter_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        收集Twitter数据
        """
        try:
            if not self.twitter_api_key:
                return []
                
            # 构建查询参数
            coin = symbol.replace('USDT', '')
            query = f"#{coin} OR #{coin.lower()} OR #{coin}USD -is:retweet lang:en"
            
            # Twitter API V2端点
            url = "https://api.twitter.com/2/tweets/search/recent"
            headers = {
                "Authorization": f"Bearer {self.twitter_api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                url,
                headers=headers,
                params={
                    'query': query,
                    'max_results': 100,
                    'tweet.fields': 'created_at,public_metrics'
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = data.get('data', [])
                    
                    # 处理推文数据
                    processed_tweets = []
                    for tweet in tweets:
                        processed_tweets.append({
                            'platform': 'twitter',
                            'text': tweet.get('text', ''),
                            'timestamp': tweet.get('created_at', ''),
                            'metrics': tweet.get('public_metrics', {}),
                            'sentiment_score': None  # 待后续分析
                        })
                        
                    return processed_tweets
                else:
                    logger.error(f"Twitter API请求失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Twitter数据收集失败: {e}")
            return []
            
    async def _collect_reddit_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        收集Reddit数据
        """
        try:
            if not self.reddit_api_key:
                return []
                
            # 构建查询参数
            coin = symbol.replace('USDT', '')
            subreddits = [f"r/{coin}", "r/cryptocurrency"]
            
            all_posts = []
            for subreddit in subreddits:
                # Reddit API端点
                url = f"https://www.reddit.com/{subreddit}/new.json"
                headers = {
                    "User-Agent": "Crypto Sentiment Bot 1.0"
                }
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get('data', {}).get('children', [])
                        
                        # 处理帖子数据
                        for post in posts:
                            post_data = post.get('data', {})
                            all_posts.append({
                                'platform': 'reddit',
                                'text': post_data.get('title', '') + ' ' + post_data.get('selftext', ''),
                                'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                                'metrics': {
                                    'score': post_data.get('score', 0),
                                    'comments': post_data.get('num_comments', 0)
                                },
                                'sentiment_score': None  # 待后续分析
                            })
                            
            return all_posts
            
        except Exception as e:
            logger.error(f"Reddit数据收集失败: {e}")
            return []
            
    async def _collect_telegram_data(self, symbol: str) -> List[Dict[str, Any]]:
        """
        收集Telegram数据
        """
        try:
            if not self.telegram_api_key:
                return []
                
            # TODO: 实现Telegram数据收集
            # 需要预先定义要监控的群组列表
            return []
            
        except Exception as e:
            logger.error(f"Telegram数据收集失败: {e}")
            return [] 