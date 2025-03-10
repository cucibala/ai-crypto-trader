#!/usr/bin/env python3
import sys
from pathlib import Path
import logging
from decimal import Decimal

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.binance_rest_client import BinanceRestClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_market_data(client: BinanceRestClient):
    """测试市场数据接口"""
    try:
        symbol = "DOGEUSDT"
        
        # 1. 获取交易对价格
        logger.info("1. 获取交易对价格...")
        price_info = client.get_symbol_price(symbol)
        logger.info("%s 当前价格: %s", symbol, price_info['price'])
        
        # 2. 获取24小时价格统计
        logger.info("\n2. 获取24小时价格统计...")
        ticker_info = client.get_24h_ticker(symbol)
        logger.info("%s 24小时统计:", symbol)
        logger.info("最高价: %s", ticker_info['highPrice'])
        logger.info("最低价: %s", ticker_info['lowPrice'])
        logger.info("成交量: %s", ticker_info['volume'])
        logger.info("涨跌幅: %s%%", ticker_info['priceChangePercent'])
        
        # 3. 获取订单簿数据
        logger.info("\n3. 获取订单簿数据...")
        depth = client.get_order_book(symbol, limit=5)
        logger.info("买盘前5档:")
        for price, qty in depth['bids'][:5]:
            logger.info("价格: %s, 数量: %s", price, qty)
        logger.info("卖盘前5档:")
        for price, qty in depth['asks'][:5]:
            logger.info("价格: %s, 数量: %s", price, qty)
            
    except Exception as e:
        logger.error("市场数据测试失败: %s", str(e))
        raise

def test_account_data(client: BinanceRestClient):
    """测试账户数据接口"""
    try:
        # 1. 获取账户信息
        logger.info("\n1. 获取账户信息...")
        account_info = client.get_account_info()
        
        # 显示账户权限
        permissions = account_info.get('permissions', [])
        logger.info("账户权限: %s", permissions)
        
        # 显示账户佣金费率
        commission_rates = account_info.get('commissionRates', {})
        logger.info("\n账户佣金费率:")
        logger.info("Maker费率: %s", commission_rates.get('maker', 'N/A'))
        logger.info("Taker费率: %s", commission_rates.get('taker', 'N/A'))
        
        # 显示账户余额
        balances = account_info.get('balances', [])
        non_zero_balances = [
            balance for balance in balances
            if float(balance['free']) > 0 or float(balance['locked']) > 0
        ]
        
        logger.info("\n账户余额:")
        for balance in non_zero_balances:
            logger.info("%s: 可用=%s, 冻结=%s",
                       balance['asset'],
                       balance['free'],
                       balance['locked'])
            
        # 2. 获取当前挂单
        logger.info("\n2. 获取当前挂单...")
        open_orders = client.get_open_orders()
        logger.info("当前挂单数量: %d", len(open_orders))
        for order in open_orders:
            logger.info("订单信息: %s", order)
            
    except Exception as e:
        logger.error("账户数据测试失败: %s", str(e))
        raise

def test_trading(client: BinanceRestClient):
    """测试交易接口"""
    try:
        symbol = "DOGEUSDT"
        
        # 1. 获取当前价格
        price_info = client.get_symbol_price(symbol)
        current_price = Decimal(price_info['price'])
        
        # 2. 下限价单（低于市价20%，不会立即成交）
        order_price = (current_price * Decimal('0.8')).quantize(Decimal('0.000001'))
        quantity = Decimal('100')  # 100 DOGE
        
        logger.info("\n1. 测试下限价单...")
        logger.info("当前价格: %s", current_price)
        logger.info("下单价格: %s", order_price)
        logger.info("下单数量: %s", quantity)
        
        order = client.create_order(
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=quantity,
            price=order_price
        )
        logger.info("订单信息: %s", order)
        
        # 3. 查询订单状态
        logger.info("\n2. 查询订单状态...")
        order_status = client.get_order(
            symbol=symbol,
            order_id=order['orderId']
        )
        logger.info("订单状态: %s", order_status)
        
        # 4. 取消订单
        logger.info("\n3. 取消订单...")
        cancel_result = client.cancel_order(
            symbol=symbol,
            order_id=order['orderId']
        )
        logger.info("取消结果: %s", cancel_result)
        
    except Exception as e:
        logger.error("交易测试失败: %s", str(e))
        raise

def main():
    """主函数"""
    try:
        # 创建REST API客户端
        client = BinanceRestClient()
        
        # 1. 测试市场数据
        logger.info("开始测试市场数据接口...")
        test_market_data(client)
        
        # 2. 测试账户数据
        logger.info("\n开始测试账户数据接口...")
        test_account_data(client)
        
        # 3. 测试交易接口
        logger.info("\n开始测试交易接口...")
        test_trading(client)
        
        logger.info("\n测试完成 ✅")
        
    except KeyboardInterrupt:
        logger.info("程序终止")
    except Exception as e:
        logger.error("测试失败: %s", str(e))
        raise

if __name__ == '__main__':
    main() 