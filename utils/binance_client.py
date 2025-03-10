import logging
import hmac
import hashlib
import time
import json
from typing import Dict, List, Any, Optional, Callable
import aiohttp
from datetime import datetime
from urllib.parse import urlencode
import asyncio
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, _get_env_var

logger = logging.getLogger(__name__)

class BinanceClient:
    """币安API客户端（WebSocket实现）"""
    
    def __init__(self, api_key: str = BINANCE_API_KEY, api_secret: str = BINANCE_API_SECRET):
        """初始化客户端"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_base_url = "wss://ws-api.binance.com:9443"
        self.ws = None
        self.request_id = 0
        self.pending_requests = {}
        self.callbacks = {}
        self.is_connected = False
        self.heartbeat_task = None
        
        # 获取代理设置
        self.http_proxy = _get_env_var('HTTP_PROXY', required=False)
        self.https_proxy = _get_env_var('HTTPS_PROXY', required=False)
        
        if self.http_proxy or self.https_proxy:
            logger.info(f"使用代理: HTTP={self.http_proxy}, HTTPS={self.https_proxy}")
            
    def generate_signature(self, params: Dict) -> str:
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
            
    async def connect(self):
        """建立WebSocket连接"""
        if self.is_connected:
            return
            
        try:
            # 配置代理
            proxy = self.https_proxy or self.http_proxy
            connector = aiohttp.TCPConnector(ssl=False) if proxy else None
            
            # 创建会话
            session = aiohttp.ClientSession(connector=connector)
            
            # 连接WebSocket
            self.ws = await session.ws_connect(
                f"{self.ws_base_url}/ws-api/v3",
                proxy=proxy,
                heartbeat=30
            )
            
            self.is_connected = True
            logger.info("WebSocket连接成功")
            
            # 启动消息处理循环
            asyncio.create_task(self._message_handler())
            
            # 启动心跳任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat())
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {str(e)}")
            raise
            
    async def _heartbeat(self):
        """发送心跳包"""
        while self.is_connected:
            try:
                await self.ws.ping()
                await asyncio.sleep(20)
            except Exception as e:
                logger.error(f"心跳发送失败: {str(e)}")
                await self.reconnect()
                
    async def reconnect(self):
        """重新连接"""
        self.is_connected = False
        if self.ws:
            await self.ws.close()
        await self.connect()
        
    async def _message_handler(self):
        """处理WebSocket消息"""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        
                        # 处理响应消息
                        if 'id' in data:
                            request_id = data['id']
                            if request_id in self.pending_requests:
                                future = self.pending_requests.pop(request_id)
                                if 'result' in data:
                                    future.set_result(data['result'])
                                elif 'error' in data:
                                    future.set_exception(Exception(data['error']))
                                    
                        # 处理订阅消息
                        elif 'stream' in data:
                            stream = data['stream']
                            if stream in self.callbacks:
                                for callback in self.callbacks[stream]:
                                    try:
                                        await callback(data['data'])
                                    except Exception as e:
                                        logger.error(f"回调执行错误: {str(e)}")
                                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析错误: {str(e)}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket错误: {msg.data}")
                    break
                    
        except Exception as e:
            logger.error(f"消息处理错误: {str(e)}")
            await self.reconnect()
            
    async def _send_request(self, method: str, params: Optional[Dict] = None) -> Any:
        """发送WebSocket请求"""
        if not self.is_connected:
            await self.connect()
            
        self.request_id += 1
        request = {
            'id': self.request_id,
            'method': method,
            'params': params or {}
        }

        # 如果需要签名
        if method.startswith('user.'):
            timestamp = int(time.time() * 1000)
            request['params']['timestamp'] = timestamp
            request['params']['apiKey'] = self.api_key
            
            # 生成签名
            query_string = urlencode(sorted(request['params'].items()))
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            request['params']['signature'] = signature
            
        # 创建Future对象
        future = asyncio.Future()
        self.pending_requests[self.request_id] = future
        
        # 发送请求
        await self.ws.send_json(request)
        
        try:
            # 等待响应
            response = await asyncio.wait_for(future, timeout=10)
            return response
        except asyncio.TimeoutError:
            self.pending_requests.pop(self.request_id, None)
            raise Exception("请求超时")
            
    async def subscribe(self, streams: List[str], callback: Callable):
        """订阅数据流"""
        if not self.is_connected:
            await self.connect()
            
        # 注册回调
        for stream in streams:
            if stream not in self.callbacks:
                self.callbacks[stream] = []
            self.callbacks[stream].append(callback)
            
        # 发送订阅请求
        await self._send_request('SUBSCRIBE', streams)
        
    async def get_exchange_info(self) -> Dict[str, Any]:
        """获取交易所信息"""
        return await self._send_request('exchangeInfo')
        
    async def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        return await self._send_request('user.account')
        
    async def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """获取交易对价格"""
        return await self._send_request('ticker.price', {'symbol': symbol})
        
    async def create_order(self,
                          symbol: str,
                          side: str,
                          order_type: str,
                          quantity: float,
                          price: Optional[float] = None,
                          time_in_force: str = 'GTC') -> Dict[str, Any]:
        """创建订单"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        if order_type == 'LIMIT':
            if not price:
                raise ValueError("LIMIT订单必须指定价格")
            params['price'] = price
            params['timeInForce'] = time_in_force
            
        return await self._send_request('user.order.place', params)
        
    async def cancel_order(self,
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
            
        return await self._send_request('user.order.cancel', params)
        
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取当前挂单"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return await self._send_request('user.openOrders', params)
        
    async def get_order(self,
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
            
        return await self._send_request('user.order', params)
        
    async def close(self):
        """关闭连接"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            
        if self.ws:
            await self.ws.close()
            
        self.is_connected = False
        logger.info("WebSocket连接已关闭") 