import logging
from typing import Dict, List, Any
from datetime import datetime
import json
import numpy as np
import pandas as pd
from textblob import TextBlob
import openai
from config.settings import MODEL_CONFIG

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    市场情绪分析器
    集成多个维度的情绪分析：
    1. 社交媒体情绪
    2. 新闻情绪
    3. 技术指标情绪
    4. 市场深度情绪
    """
    
    def __init__(self, api_key: str):
        """
        初始化情绪分析器
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key
        openai.api_key = api_key
        self.model_config = MODEL_CONFIG
        
    async def analyze_sentiment(self,
                              market_data: Dict[str, Any],
                              news_data: List[Dict[str, Any]],
                              social_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        综合分析市场情绪
        
        Args:
            market_data: 市场数据
            news_data: 新闻数据
            social_data: 社交媒体数据
            
        Returns:
            Dict: 情绪分析结果
        """
        try:
            # 分析各个维度的情绪
            technical_sentiment = self._analyze_technical_sentiment(market_data)
            news_sentiment = await self._analyze_news_sentiment(news_data)
            social_sentiment = self._analyze_social_sentiment(social_data)
            market_depth_sentiment = self._analyze_market_depth_sentiment(market_data)
            
            # 使用GPT综合分析各维度情绪
            combined_sentiment = await self._combine_sentiment_analysis(
                technical_sentiment,
                news_sentiment,
                social_sentiment,
                market_depth_sentiment
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": market_data.get("symbol"),
                "technical_sentiment": technical_sentiment,
                "news_sentiment": news_sentiment,
                "social_sentiment": social_sentiment,
                "market_depth_sentiment": market_depth_sentiment,
                "combined_sentiment": combined_sentiment
            }
            
        except Exception as e:
            logger.error(f"情绪分析失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def _analyze_technical_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析技术指标情绪
        """
        try:
            # 提取技术指标
            rsi = market_data.get('rsi', 50)
            macd = market_data.get('macd', 0)
            bollinger_position = market_data.get('bollinger_position', 0)
            
            # RSI情绪判断
            rsi_sentiment = 'bullish' if rsi < 30 else ('bearish' if rsi > 70 else 'neutral')
            
            # MACD情绪判断
            macd_sentiment = 'bullish' if macd > 0 else ('bearish' if macd < 0 else 'neutral')
            
            # 布林带位置情绪判断
            bb_sentiment = 'bullish' if bollinger_position < -1 else ('bearish' if bollinger_position > 1 else 'neutral')
            
            # 计算综合技术情绪
            sentiment_scores = {
                'bullish': 1,
                'neutral': 0,
                'bearish': -1
            }
            
            avg_score = np.mean([
                sentiment_scores[rsi_sentiment],
                sentiment_scores[macd_sentiment],
                sentiment_scores[bb_sentiment]
            ])
            
            overall_sentiment = 'bullish' if avg_score > 0.3 else ('bearish' if avg_score < -0.3 else 'neutral')
            
            return {
                'overall': overall_sentiment,
                'confidence': abs(avg_score),
                'indicators': {
                    'rsi': {
                        'value': rsi,
                        'sentiment': rsi_sentiment
                    },
                    'macd': {
                        'value': macd,
                        'sentiment': macd_sentiment
                    },
                    'bollinger_bands': {
                        'position': bollinger_position,
                        'sentiment': bb_sentiment
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"技术情绪分析失败: {e}")
            return {
                'overall': 'neutral',
                'confidence': 0,
                'error': str(e)
            }
            
    async def _analyze_news_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析新闻情绪
        """
        try:
            if not news_data:
                return {
                    'overall': 'neutral',
                    'confidence': 0,
                    'reason': '没有新闻数据'
                }
                
            # 构建新闻摘要
            news_summary = "\n".join(
                f"- {news['title']}: {news['summary']}"
                for news in news_data
            )
            
            # 使用GPT分析新闻情绪
            prompt = f"""
            请分析以下加密货币相关新闻的市场情绪：
            
            {news_summary}
            
            请从以下几个方面进行分析：
            1. 整体市场情绪（积极/消极/中性）
            2. 主要影响因素
            3. 潜在市场影响
            
            请以JSON格式返回分析结果，包含以下字段：
            - sentiment: 整体情绪 (bullish/bearish/neutral)
            - confidence: 置信度 (0-1)
            - key_factors: 关键影响因素列表
            - potential_impact: 潜在市场影响
            - reasoning: 分析理由
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_config["model"],
                messages=[
                    {"role": "system", "content": "你是一个专业的市场新闻分析师，擅长分析新闻对市场的影响。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )
            
            analysis = self._parse_gpt_response(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            logger.error(f"新闻情绪分析失败: {e}")
            return {
                'overall': 'neutral',
                'confidence': 0,
                'error': str(e)
            }
            
    def _analyze_social_sentiment(self, social_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析社交媒体情绪
        """
        try:
            if not social_data:
                return {
                    'overall': 'neutral',
                    'confidence': 0,
                    'reason': '没有社交媒体数据'
                }
                
            # 使用TextBlob进行情感分析
            sentiments = []
            for post in social_data:
                text = post.get('text', '')
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
                
            # 计算平均情绪
            avg_sentiment = np.mean(sentiments)
            sentiment_std = np.std(sentiments)
            
            # 确定整体情绪
            if avg_sentiment > 0.1:
                overall = 'bullish'
            elif avg_sentiment < -0.1:
                overall = 'bearish'
            else:
                overall = 'neutral'
                
            # 计算置信度
            confidence = min(abs(avg_sentiment) * 2, 1.0)
            
            return {
                'overall': overall,
                'confidence': confidence,
                'metrics': {
                    'average_sentiment': avg_sentiment,
                    'sentiment_std': sentiment_std,
                    'total_posts': len(social_data)
                }
            }
            
        except Exception as e:
            logger.error(f"社交媒体情绪分析失败: {e}")
            return {
                'overall': 'neutral',
                'confidence': 0,
                'error': str(e)
            }
            
    def _analyze_market_depth_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场深度情绪
        """
        try:
            bids = market_data.get('bids', [])
            asks = market_data.get('asks', [])
            
            if not bids or not asks:
                return {
                    'overall': 'neutral',
                    'confidence': 0,
                    'reason': '没有市场深度数据'
                }
                
            # 计算买卖压力
            bid_volume = sum(float(bid[1]) for bid in bids[:5])  # 前5档买单量
            ask_volume = sum(float(ask[1]) for ask in asks[:5])  # 前5档卖单量
            
            # 计算买卖比率
            volume_ratio = bid_volume / ask_volume if ask_volume > 0 else 1
            
            # 判断情绪
            if volume_ratio > 1.2:  # 买压明显大于卖压
                sentiment = 'bullish'
                confidence = min((volume_ratio - 1) / 2, 1.0)
            elif volume_ratio < 0.8:  # 卖压明显大于买压
                sentiment = 'bearish'
                confidence = min((1 - volume_ratio) / 2, 1.0)
            else:
                sentiment = 'neutral'
                confidence = 1 - abs(volume_ratio - 1)
                
            return {
                'overall': sentiment,
                'confidence': confidence,
                'metrics': {
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'volume_ratio': volume_ratio
                }
            }
            
        except Exception as e:
            logger.error(f"市场深度情绪分析失败: {e}")
            return {
                'overall': 'neutral',
                'confidence': 0,
                'error': str(e)
            }
            
    async def _combine_sentiment_analysis(self,
                                        technical_sentiment: Dict[str, Any],
                                        news_sentiment: Dict[str, Any],
                                        social_sentiment: Dict[str, Any],
                                        market_depth_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        综合各维度的情绪分析
        """
        try:
            # 构建情绪分析摘要
            sentiment_summary = {
                'technical': technical_sentiment,
                'news': news_sentiment,
                'social': social_sentiment,
                'market_depth': market_depth_sentiment
            }
            
            # 使用GPT综合分析
            prompt = f"""
            请综合分析以下各维度的市场情绪数据：
            
            {json.dumps(sentiment_summary, indent=2, ensure_ascii=False)}
            
            请从以下几个方面进行分析：
            1. 综合市场情绪判断
            2. 各维度情绪的权重和重要性
            3. 潜在的市场影响
            4. 可能的市场机会或风险
            
            请以JSON格式返回分析结果，包含以下字段：
            - overall_sentiment: 综合情绪 (bullish/bearish/neutral)
            - confidence: 置信度 (0-1)
            - dimension_weights: 各维度权重
            - market_implications: 市场影响分析
            - opportunities: 市场机会
            - risks: 潜在风险
            - reasoning: 分析理由
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.model_config["model"],
                messages=[
                    {"role": "system", "content": "你是一个专业的市场情绪分析专家，擅长综合分析各种市场情绪指标。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config["temperature"],
                max_tokens=self.model_config["max_tokens"]
            )
            
            analysis = self._parse_gpt_response(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            logger.error(f"综合情绪分析失败: {e}")
            return {
                'overall_sentiment': 'neutral',
                'confidence': 0,
                'error': str(e)
            }
            
    def _parse_gpt_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析GPT响应
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            try:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response_text[start:end]
                    return json.loads(json_str)
            except:
                pass
            return {"raw_response": response_text} 