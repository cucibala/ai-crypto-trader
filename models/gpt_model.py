import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from openai import OpenAI
from config.settings import MODEL_CONFIG
from models.base_model import BaseModel

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 创建格式化器
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 将格式化器添加到处理器
console_handler.setFormatter(formatter)

# 将处理器添加到日志记录器
if not logger.handlers:
    logger.addHandler(console_handler)

logger.debug("GPT模型日志系统初始化完成")

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
        logger.info(f"初始化 GPT 模型，使用模型: {self.model_config['model']}, API基础URL: {base_url}")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            organization=self.model_config['org_id'] if self.model_config['org_id'] else None
        )
        logger.info("GPT 模型初始化完成")
        
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场数据
        """
        try:
            logger.info(f"开始分析市场数据: {market_data['symbol']}")
            
            # 构建市场数据摘要
            market_summary = self._prepare_market_summary(market_data)
            logger.debug(f"市场数据摘要:\n{market_summary}")
            
            # 构建分析提示
            prompt = self._build_analysis_prompt(market_summary)
            logger.debug(f"分析提示:\n{prompt}")
            
            # 调用GPT进行分析
            logger.info("正在调用 GPT API 进行市场分析...")
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
            raw_response = response.choices[0].message.content
            logger.debug(f"GPT 原始响应:\n{raw_response}")
            
            analysis = self._parse_gpt_response(raw_response)
            logger.info(f"市场分析完成，趋势: {analysis.get('trend', 'unknown')}")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": market_data["symbol"],
                "analysis": analysis
            }
            logger.debug(f"完整分析结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            logger.error(f"市场分析失败: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def generate_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成交易策略
        """
        try:
            logger.info("开始生成交易策略")
            
            # 构建策略生成提示
            prompt = self._build_strategy_prompt(analysis_result)
            logger.debug(f"策略生成提示:\n{prompt}")
            
            logger.info("正在调用 GPT API 生成策略...")
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的量化交易策略师，擅长制定风险可控的交易策略。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            raw_response = response.choices[0].message.content
            logger.debug(f"GPT 原始响应:\n{raw_response}")
            
            strategy = self._parse_gpt_response(raw_response)
            logger.info(f"策略生成完成，建议操作: {strategy.get('action', 'unknown')}")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "strategy": strategy
            }
            logger.debug(f"完整策略:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            logger.error(f"策略生成失败: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def evaluate_risk(self, strategy: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估策略风险
        """
        try:
            logger.info("开始评估策略风险")
            
            # 构建风险评估提示
            prompt = self._build_risk_prompt(strategy, portfolio)
            logger.debug(f"风险评估提示:\n{prompt}")
            
            logger.info("正在调用 GPT API 评估风险...")
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的风险管理专家，擅长评估交易策略的风险。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            raw_response = response.choices[0].message.content
            logger.debug(f"GPT 原始响应:\n{raw_response}")
            
            risk_assessment = self._parse_gpt_response(raw_response)
            logger.info(f"风险评估完成，风险等级: {risk_assessment.get('risk_level', 'unknown')}")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "risk_assessment": risk_assessment
            }
            logger.debug(f"完整风险评估:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            logger.error(f"风险评估失败: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def optimize_parameters(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        优化模型参数
        """
        try:
            logger.info("开始优化模型参数")
            data_points = len(historical_data)
            time_range = f"{historical_data[0]['timestamp']} 到 {historical_data[-1]['timestamp']}"
            logger.info(f"历史数据: {data_points} 个数据点, 时间范围: {time_range}")
            
            # 构建参数优化提示
            prompt = self._build_optimization_prompt(historical_data)
            logger.debug(f"参数优化提示:\n{prompt}")
            
            logger.info("正在调用 GPT API 优化参数...")
            response = self.client.chat.completions.create(
                model=self.model_config['model'],
                messages=[
                    {"role": "system", "content": "你是一个专业的量化交易系统优化专家，擅长优化交易策略参数。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config['temperature'],
                max_tokens=self.model_config['max_tokens']
            )
            
            raw_response = response.choices[0].message.content
            logger.debug(f"GPT 原始响应:\n{raw_response}")
            
            optimized_params = self._parse_gpt_response(raw_response)
            logger.info("参数优化完成")
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "optimized_parameters": optimized_params
            }
            logger.debug(f"完整优化结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            logger.error(f"参数优化失败: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    def _prepare_market_summary(self, market_data: Dict[str, Any]) -> str:
        """
        准备市场数据摘要
        """
        try:
            required_fields = [
                'price', 'price_change_24h', 'volume_24h', 'quote_volume',
                'volume_change_24h', 'volume_vs_7d_avg', 'rsi', 'macd',
                'bollinger_position', 'price_trends', 'buy_depth', 'sell_depth'
            ]
            
            for field in required_fields:
                if field not in market_data:
                    raise ValueError(f"缺少必要的市场数据字段: {field}")
            
            # 构建多时间维度的技术分析摘要
            technical_summary = {
                '日线': {
                    'RSI': market_data['rsi']['1d'],
                    'MACD': market_data['macd']['1d'],
                    'Bollinger': market_data['bollinger_position']['1d'],
                    'MA趋势': market_data['price_trends']['1d'].get('trend', 'unknown'),
                    '价格位置': market_data['price_trends']['1d'].get('price_position', 'unknown'),
                    '30日高点': market_data['price_trends']['1d'].get('high_30d', 'N/A'),
                    '30日低点': market_data['price_trends']['1d'].get('low_30d', 'N/A')
                },
                '4小时': {
                    'RSI': market_data['rsi']['4h'],
                    'MACD': market_data['macd']['4h'],
                    'Bollinger': market_data['bollinger_position']['4h'],
                    'MA趋势': market_data['price_trends']['4h'].get('trend', 'unknown'),
                    '价格位置': market_data['price_trends']['4h'].get('price_position', 'unknown'),
                    '7日高点': market_data['price_trends']['4h'].get('high_7d', 'N/A'),
                    '7日低点': market_data['price_trends']['4h'].get('low_7d', 'N/A')
                },
                '1小时': {
                    'RSI': market_data['rsi']['1h'],
                    'MACD': market_data['macd']['1h'],
                    'Bollinger': market_data['bollinger_position']['1h'],
                    'MA趋势': market_data['price_trends']['1h'].get('trend', 'unknown'),
                    '价格位置': market_data['price_trends']['1h'].get('price_position', 'unknown'),
                    '24小时高点': market_data['price_trends']['1h'].get('high_24h', 'N/A'),
                    '24小时低点': market_data['price_trends']['1h'].get('low_24h', 'N/A')
                }
            }
            
            # 记录技术分析摘要
            logger.debug(f"技术分析摘要: {json.dumps(technical_summary, indent=2, ensure_ascii=False)}")
            
            # 计算买卖压力
            total_buy_volume = sum(float(price) * float(qty) for price, qty in market_data['buy_depth'])
            total_sell_volume = sum(float(price) * float(qty) for price, qty in market_data['sell_depth'])
            buy_sell_ratio = total_buy_volume / total_sell_volume if total_sell_volume > 0 else 1
            
            market_summary = f"""
当前市场状况分析：

1. 价格数据：
- 当前价格：{market_data['price']} USDT
- 24小时涨跌幅：{market_data['price_change_24h']}%
- 买卖盘压力比：{buy_sell_ratio:.2f}（大于1表示买压更大）

2. 成交量分析：
- 24小时成交量：{market_data['volume_24h']} BTC
- 成交量变化：{market_data['volume_change_24h']}%
- 相对7日均量：{market_data['volume_vs_7d_avg']}%
- 24小时成交额：{market_data['quote_volume']} USDT

3. 技术指标多维度分析：

日线周期：
- RSI: {technical_summary['日线']['RSI']}
- MACD: {technical_summary['日线']['MACD']}
- 布林带位置: {technical_summary['日线']['Bollinger']}%
- MA趋势: {technical_summary['日线']['MA趋势']}
- 价格位置: {technical_summary['日线']['价格位置']}
- 30日价格区间: {technical_summary['日线']['30日低点']} - {technical_summary['日线']['30日高点']}

4小时周期：
- RSI: {technical_summary['4小时']['RSI']}
- MACD: {technical_summary['4小时']['MACD']}
- 布林带位置: {technical_summary['4小时']['Bollinger']}%
- MA趋势: {technical_summary['4小时']['MA趋势']}
- 价格位置: {technical_summary['4小时']['价格位置']}
- 7日价格区间: {technical_summary['4小时']['7日低点']} - {technical_summary['4小时']['7日高点']}

1小时周期：
- RSI: {technical_summary['1小时']['RSI']}
- MACD: {technical_summary['1小时']['MACD']}
- 布林带位置: {technical_summary['1小时']['Bollinger']}%
- MA趋势: {technical_summary['1小时']['MA趋势']}
- 价格位置: {technical_summary['1小时']['价格位置']}
- 24小时价格区间: {technical_summary['1小时']['24小时低点']} - {technical_summary['1小时']['24小时高点']}

请基于以上数据进行全面分析，并给出以下建议：
1. 主要趋势判断（多个时间维度）
2. 支撑位和阻力位（基于价格区间和技术指标）
3. 建议的交易方向和具体策略
4. 入场价格区间（基于技术指标和市场结构）
5. 止损位（至少距离入场价2%以上）
6. 止盈目标（基于支撑/阻力位，设置多个目标）
7. 风险等级评估（1-5，考虑趋势背离、波动性等因素）
8. 建议的持仓时间
9. 需要特别注意的风险因素

请确保建议具有实际操作价值，止损和止盈的设置要考虑市场波动性，不要过于保守。同时要充分考虑多个时间维度的趋势，确保交易方向与主趋势一致。
"""
            return market_summary
        except Exception as e:
            logger.error(f"准备市场数据摘要时出错: {str(e)}", exc_info=True)
            raise
        
    def _build_analysis_prompt(self, market_summary: str) -> str:
        """
        构建分析提示
        """
        logger.info("开始构建市场分析提示")
        
        prompt = f"""
        请基于以下市场数据进行深入分析：
        
        {market_summary}
        
        请从以下几个方面进行分析：
        1. 市场趋势判断
        2. 支撑位和阻力位
        3. 成交量分析
        4. 技术指标解读
        5. 市场情绪评估
        
        请以JSON格式返回分析结果，必须包含以下字段：
        {{
            "trend": "市场趋势 (bullish/bearish/neutral)",
            "support_levels": [支撑位列表],
            "resistance_levels": [阻力位列表],
            "volume_analysis": {{
                "volume_trend": "成交量趋势",
                "volume_conclusion": "成交量分析结论"
            }},
            "technical_indicators": {{
                "rsi_analysis": "RSI分析结论",
                "macd_analysis": "MACD分析结论",
                "bollinger_analysis": "布林带分析结论"
            }},
            "market_sentiment": "市场情绪分析",
            "confidence": "分析置信度 (0-1)",
            "reasoning": "详细分析理由"
        }}
        
        注意：请确保返回格式严格符合JSON规范，所有字段都必须填写。
        """
        
        logger.debug(f"生成的分析提示:\n{prompt}")
        return prompt
        
    def _build_strategy_prompt(self, analysis_result: Dict[str, Any]) -> str:
        """
        构建策略生成提示
        """
        logger.info("开始构建策略生成提示")
        logger.debug(f"输入的分析结果: {json.dumps(analysis_result, indent=2, ensure_ascii=False)}")
        
        prompt = f"""
        请基于以下市场分析结果生成交易策略：
        
        {json.dumps(analysis_result, indent=2, ensure_ascii=False)}
        
        请从以下几个方面制定策略：
        1. 交易方向
        2. 入场价格
        3. 止损价格
        4. 止盈目标
        5. 仓位大小
        
        请以JSON格式返回策略，必须包含以下字段：
        {{
            "action": "交易动作 (buy/sell/hold)",
            "entry_price": "入场价格",
            "stop_loss": "止损价格",
            "take_profit": "止盈价格",
            "position_size": "仓位大小 (占总资金百分比)",
            "time_frame": "持仓时间框架",
            "conditions": [
                "执行条件1",
                "执行条件2",
                "..."
            ],
            "risk_level": "风险等级 (1-5)",
            "reasoning": "详细策略理由"
        }}
        
        注意：请确保返回格式严格符合JSON规范，所有字段都必须填写。
        """
        
        logger.debug(f"生成的策略提示:\n{prompt}")
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
            logger.debug("尝试解析 GPT 响应...")
            result = json.loads(response_text)
            logger.debug("JSON 解析成功")
            return result
        except json.JSONDecodeError:
            logger.warning("直接 JSON 解析失败，尝试提取 JSON 部分...")
            try:
                # 查找第一个{和最后一个}之间的内容
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response_text[start:end]
                    result = json.loads(json_str)
                    logger.debug("JSON 部分提取和解析成功")
                    return result
            except:
                logger.error("JSON 提取和解析失败")
                pass
                
            # 如果仍然失败，返回原始文本
            logger.warning("返回原始响应文本")
            return {"raw_response": response_text}