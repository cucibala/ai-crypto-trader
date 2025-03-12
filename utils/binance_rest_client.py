import logging
import hmac
import hashlib
import time
import json
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime
from urllib.parse import urlencode
from decimal import Decimal
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, _get_env_var

logger = logging.getLogger(__name__)

class BinanceRestClient:
    """币安 REST API 客户端"""
    
    def __init__(self, api_key: str = BINANCE_API_KEY, api_secret: str = BINANCE_API_SECRET):
        """初始化客户端"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"
        
        # 获取代理设置
        self.http_proxy = _get_env_var('HTTP_PROXY', required=False)
        self.https_proxy = _get_env_var('HTTPS_PROXY', required=False)
        
        self.proxies = {}
        if self.http_proxy:
            self.proxies['http'] = self.http_proxy
        if self.https_proxy:
            self.proxies['https'] = self.https_proxy
            
        if self.proxies:
            logger.info("使用代理: %s", self.proxies)
            
    def _get_timestamp(self) -> int:
        """获取时间戳"""
        return int(time.time() * 1000)
        
    def _generate_signature(self, params: Dict) -> str:
        """生成请求签名"""
        # 将参数转换为查询字符串
        query_string = urlencode(sorted(params.items()))
        
        # 使用HMAC-SHA256算法生成签名
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
        
    def _handle_response(self, response: requests.Response) -> Any:
        """处理响应"""
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            logger.error("API请求失败: %s", error)
            raise Exception(f"API请求失败: {error}")
            
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Any:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if signed:
            # 添加时间戳和API密钥
            params = params or {}
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._generate_signature(params)
            headers['X-MBX-APIKEY'] = self.api_key
            
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                proxies=self.proxies,
                verify=False if self.proxies else True
            )
            return self._handle_response(response)
            
        except Exception as e:
            logger.error("请求失败: %s", str(e))
            raise
            
    def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息"""
        return self._request('GET', '/api/v3/exchangeInfo')
        
    def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """获取交易对价格"""
        return self._request('GET', '/api/v3/ticker/price', {'symbol': symbol})
        
    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        return self._request('GET', '/api/v3/account', {}, signed=True)
        
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当前挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v3/openOrders', params, signed=True)
        
    def create_order(self,
                    symbol: str,
                    side: str,
                    order_type: str,
                    quantity: Decimal,
                    price: Optional[Decimal] = None,
                    time_in_force: str = 'GTC') -> Dict[str, Any]:
        """创建订单"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': str(quantity)
        }
        
        if order_type == 'LIMIT':
            if not price:
                raise ValueError("限价单必须指定价格")
            params['price'] = str(price)
            params['timeInForce'] = time_in_force
            
        return self._request('POST', '/api/v3/order', params, signed=True)
        
    def cancel_order(self,
                    symbol: str,
                    order_id: Optional[int] = None,
                    orig_client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """取消订单"""
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        elif orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        else:
            raise ValueError("必须指定order_id或orig_client_order_id")
            
        return self._request('DELETE', '/api/v3/order', params, signed=True)
        
    def get_order(self,
                 symbol: str,
                 order_id: Optional[int] = None,
                 orig_client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """查询订单状态"""
        params = {'symbol': symbol}
        
        if order_id:
            params['orderId'] = order_id
        elif orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        else:
            raise ValueError("必须指定order_id或orig_client_order_id")
            
        return self._request('GET', '/api/v3/order', params, signed=True)
        
    def get_klines(self,
                  symbol: str,
                  interval: str,
                  limit: int = 500,
                  start_time: Optional[int] = None,
                  end_time: Optional[int] = None) -> List[List]:
        """获取K线数据"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
            
        return self._request('GET', '/api/v3/klines', params)
        
    def get_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取24小时价格变动情况"""
        return self._request('GET', '/api/v3/ticker/24hr', {'symbol': symbol})
        
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """获取订单簿"""
        return self._request('GET', '/api/v3/depth', {'symbol': symbol, 'limit': limit}) 