import logging
from typing import Dict, List
import json

import openai
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, api_key: str):
        """
        初始化市场分析器
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key
        openai.api_key = api_key
        
    async def analyze_market_data(self, 
                                price_data: Dict,
                                klines_data: List[Dict],
                                order_book_data: Dict) -> Dict:
        """
        分析市场数据
        
        Args:
            price_data: 实时价格数据
            klines_data: K线数据
            order_book_data: 订单簿数据
            
        Returns:
            Dict: 分析结果
        """
        try:
            # 构建市场数据摘要
            market_summary = self._prepare_market_summary(
                price_data,
                klines_data,
                order_book_data
            )
            
            # 使用OpenAI API进行分析
            analysis = await self._get_ai_analysis(market_summary)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": price_data["symbol"],
                "current_price": price_data["price"],
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"市场分析过程中出错: {e}")
            return None
            
    def _prepare_market_summary(self,
                              price_data: Dict,
                              klines_data: List[Dict],
                              order_book_data: Dict) -> str:
        """
        准备市场数据摘要
        """
        # 计算价格变化
        price_change = None
        if len(klines_data) > 1:
            first_price = klines_data[0]["open"]
            last_price = klines_data[-1]["close"]
            price_change = ((last_price - first_price) / first_price) * 100
            
        # 分析订单簿深度
        total_bid_volume = sum(bid[1] for bid in order_book_data["bids"][:5])
        total_ask_volume = sum(ask[1] for ask in order_book_data["asks"][:5])
        
        # 构建市场摘要文本
        summary = f"""
        交易对: {price_data['symbol']}
        当前价格: {price_data['price']}
        24小时价格变化: {price_change:.2f}% (如果有数据)
        
        订单簿分析:
        - 前5档买单总量: {total_bid_volume:.2f}
        - 前5档卖单总量: {total_ask_volume:.2f}
        - 买卖比例: {(total_bid_volume/total_ask_volume if total_ask_volume > 0 else 0):.2f}
        
        K线数据:
        - 最高价: {max(k['high'] for k in klines_data)}
        - 最低价: {min(k['low'] for k in klines_data)}
        - 成交量: {sum(k['volume'] for k in klines_data)}
        """
        
        return summary
        
    async def _get_ai_analysis(self, market_summary: str) -> Dict:
        """
        使用OpenAI API进行市场分析
        """
        try:
            prompt = f"""
            作为一个加密货币交易专家，请基于以下市场数据进行分析，并给出交易建议：
            
            {market_summary}
            
            请从以下几个方面进行分析：
            1. 市场趋势判断
            2. 支撑位和阻力位分析
            3. 短期价格走势预测
            4. 建议的交易操作
            5. 风险提示
            
            请以JSON格式返回分析结果，包含以下字段：
            - trend: 市场趋势 (bullish/bearish/neutral)
            - support_level: 支撑位
            - resistance_level: 阻力位
            - prediction: 短期预测
            - action: 建议操作 (buy/sell/hold)
            - risk_level: 风险等级 (1-5)
            - reasoning: 分析理由
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的加密货币市场分析师。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 解析API响应
            analysis_text = response.choices[0].message.content
            try:
                analysis_json = json.loads(analysis_text)
                return analysis_json
            except json.JSONDecodeError:
                logger.error("AI响应解析失败，返回原始文本")
                return {"raw_analysis": analysis_text}
                
        except Exception as e:
            logger.error(f"AI分析过程中出错: {e}")
            return {
                "error": str(e),
                "trend": "neutral",
                "action": "hold",
                "risk_level": 5
            }
            
    async def get_sentiment_analysis(self, news_data: List[Dict]) -> Dict:
        """
        分析市场情绪
        
        Args:
            news_data: 新闻数据列表
            
        Returns:
            Dict: 情绪分析结果
        """
        try:
            # 构建新闻摘要
            news_summary = "\n".join(
                f"- {news['title']}: {news['summary']}"
                for news in news_data
            )
            
            prompt = f"""
            请分析以下加密货币相关新闻，并评估市场情绪：
            
            {news_summary}
            
            请以JSON格式返回分析结果，包含以下字段：
            - sentiment: 整体情绪 (positive/negative/neutral)
            - confidence: 置信度 (0-1)
            - key_factors: 关键影响因素列表
            - summary: 简要分析
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的市场情绪分析师。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            sentiment_text = response.choices[0].message.content
            try:
                sentiment_json = json.loads(sentiment_text)
                return sentiment_json
            except json.JSONDecodeError:
                return {"raw_sentiment": sentiment_text}
                
        except Exception as e:
            logger.error(f"情绪分析过程中出错: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "error": str(e)
            } 