from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """
    AI模型基类，定义所有模型必须实现的接口
    """
    
    @abstractmethod
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            market_data: 市场数据字典，包含价格、交易量等信息
            
        Returns:
            Dict: 分析结果
        """
        pass
        
    @abstractmethod
    async def generate_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据分析结果生成交易策略
        
        Args:
            analysis_result: 市场分析结果
            
        Returns:
            Dict: 交易策略
        """
        pass
        
    @abstractmethod
    async def evaluate_risk(self, strategy: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估策略风险
        
        Args:
            strategy: 交易策略
            portfolio: 当前投资组合状态
            
        Returns:
            Dict: 风险评估结果
        """
        pass
        
    @abstractmethod
    async def optimize_parameters(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        优化模型参数
        
        Args:
            historical_data: 历史数据列表
            
        Returns:
            Dict: 优化后的参数
        """
        pass 