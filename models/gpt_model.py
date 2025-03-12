import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from openai import OpenAI
from config.settings import MODEL_CONFIG
from models.base_model import BaseModel

logger = logging.getLogger(__name__)

class GPTModel(BaseModel):
    """
    基于GPT的市场分析模型
    """
    
    def __init__(self, api_key: str):
        """
        初始化GPT模型
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key
        self.model_config = MODEL_CONFIG['openai']
        
        # 配置OpenAI客户端
        base_url = MODEL_CONFIG['proxy']['url'] if MODEL_CONFIG['proxy']['url'] else "https://api.openai.com/v1"
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=self.model_config['org_id'] if self.model_config['org_id'] else None
        )
        
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场数据
        """
        try:
            # 构建市场数据摘要
            market_summary = self._prepare_market_summary(market_data)
            
            # 构建分析提示
            prompt = self._build_analysis_prompt(market_summary)
            
            # 调用GPT进行分析
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的加密货币市场分析师，擅长技术分析和市场情绪分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            # 解析响应
            analysis = self._parse_gpt_response(response.choices[0].message.content)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "symbol": market_data["symbol"],
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"市场分析失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def generate_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成交易策略
        """
        try:
            # 构建策略生成提示
            prompt = self._build_strategy_prompt(analysis_result)
            
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的量化交易策略师，擅长制定风险可控的交易策略。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            strategy = self._parse_gpt_response(response.choices[0].message.content)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy
            }
            
        except Exception as e:
            logger.error(f"策略生成失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def evaluate_risk(self, strategy: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估策略风险
        """
        try:
            # 构建风险评估提示
            prompt = self._build_risk_prompt(strategy, portfolio)
            
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的风险管理专家，擅长评估交易策略的风险。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            risk_assessment = self._parse_gpt_response(response.choices[0].message.content)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "risk_assessment": risk_assessment
            }
            
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def optimize_parameters(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        优化模型参数
        """
        try:
            # 构建参数优化提示
            prompt = self._build_optimization_prompt(historical_data)
            
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的量化交易系统优化专家，擅长优化交易策略参数。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            optimized_params = self._parse_gpt_response(response.choices[0].message.content)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "optimized_parameters": optimized_params
            }
            
        except Exception as e:
            logger.error(f"参数优化失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def _prepare_market_summary(self, market_data: Dict[str, Any]) -> str:
        """
        准备市场数据摘要
        """
        summary = f"""
        交易对: {market_data.get('symbol')}
        当前价格: {market_data.get('price')}
        24小时变化: {market_data.get('price_change_24h', 0)}%
        
        交易量信息:
        - 24小时交易量: {market_data.get('volume_24h', 0)}
        - 买单量: {market_data.get('buy_volume', 0)}
        - 卖单量: {market_data.get('sell_volume', 0)}
        
        技术指标:
        - RSI: {market_data.get('rsi', 'N/A')}
        - MACD: {market_data.get('macd', 'N/A')}
        - 布林带位置: {market_data.get('bollinger_position', 'N/A')}
        
        市场深度:
        - 买单深度: {market_data.get('buy_depth', [])}
        - 卖单深度: {market_data.get('sell_depth', [])}
        """
        return summary
        
    def _build_analysis_prompt(self, market_summary: str) -> str:
        """
        构建分析提示
        """
        prompt = f"""
        请基于以下市场数据进行深入分析：
        
        {market_summary}
        
        请从以下几个方面进行分析：
        1. 市场趋势判断
        2. 支撑位和阻力位
        3. 成交量分析
        4. 技术指标解读
        5. 市场情绪评估
        
        请以JSON格式返回分析结果，包含以下字段：
        - trend: 市场趋势 (bullish/bearish/neutral)
        - support_levels: 支撑位列表
        - resistance_levels: 阻力位列表
        - volume_analysis: 成交量分析
        - technical_indicators: 技术指标分析
        - market_sentiment: 市场情绪
        - confidence: 分析置信度 (0-1)
        - reasoning: 分析理由
        """
        return prompt
        
    def _build_strategy_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        构建策略生成提示
        """
        prompt = f"""
        请基于以下市场分析结果生成交易策略：
        
        {json.dumps(analysis_result, indent=2, ensure_ascii=False)}
        
        请从以下几个方面制定策略：
        1. 交易方向
        2. 入场价格
        3. 止损价格
        4. 止盈目标
        5. 仓位大小
        
        请以JSON格式返回策略，包含以下字段：
        - action: 交易动作 (buy/sell/hold)
        - entry_price: 入场价格
        - stop_loss: 止损价格
        - take_profit: 止盈价格
        - position_size: 仓位大小 (占总资金百分比)
        - time_frame: 持仓时间框架
        - conditions: 执行条件
        - reasoning: 策略理由
        """
        return prompt
        
    def _build_risk_prompt(self, strategy: Dict[str, Any], portfolio: Dict[str, Any]) -> str:
        """
        构建风险评估提示
        """
        prompt = f"""
        请评估以下交易策略的风险：
        
        策略：
        {json.dumps(strategy, indent=2, ensure_ascii=False)}
        
        当前投资组合：
        {json.dumps(portfolio, indent=2, ensure_ascii=False)}
        
        请从以下几个方面评估风险：
        1. 潜在损失
        2. 风险收益比
        3. 投资组合影响
        4. 市场风险
        5. 执行风险
        
        请以JSON格式返回评估结果，包含以下字段：
        - risk_level: 风险等级 (1-5)
        - potential_loss: 潜在损失 (百分比)
        - risk_reward_ratio: 风险收益比
        - portfolio_impact: 对投资组合的影响
        - market_risks: 市场风险因素
        - execution_risks: 执行风险因素
        - recommendations: 风险控制建议
        """
        return prompt
        
    def _build_optimization_prompt(self, historical_data: List[Dict[str, Any]]) -> str:
        """
        构建参数优化提示
        """
        prompt = f"""
        请基于以下历史数据优化策略参数：
        
        {json.dumps(historical_data, indent=2, ensure_ascii=False)}
        
        请从以下几个方面进行优化：
        1. 技术指标参数
        2. 入场条件
        3. 止损止盈设置
        4. 仓位管理参数
        
        请以JSON格式返回优化结果，包含以下字段：
        - technical_params: 技术指标参数
        - entry_conditions: 入场条件参数
        - exit_conditions: 出场条件参数
        - position_params: 仓位管理参数
        - optimization_metrics: 优化指标
        - reasoning: 优化理由
        """
        return prompt
        
    def _parse_gpt_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析GPT响应
        """
        try:
            # 尝试直接解析JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果失败，尝试提取JSON部分
            try:
                # 查找第一个{和最后一个}之间的内容
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response_text[start:end]
                    return json.loads(json_str)
            except:
                pass
                
            # 如果仍然失败，返回原始文本
            return {"raw_response": response_text} 