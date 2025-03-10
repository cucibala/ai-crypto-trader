#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
import logging
from datetime import datetime
from decimal import Decimal

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.trader.trading_system import TradingSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_trading_system():
    """测试交易系统功能"""
    trading_system = None
    try:
        # 创建交易系统实例
        trading_system = TradingSystem()
        
        # 1. 测试系统启动
        logger.info("1. 测试系统启动...")
        await trading_system.start()
        
        # 2. 测试账户摘要
        logger.info("2. 获取账户摘要...")
        account_summary = await trading_system.get_account_summary()
        logger.info("账户摘要: %s", account_summary)
        
        # 3. 测试下限价单
        symbol = "BTCUSDT"
        logger.info("3. 测试下限价单 (%s)...", symbol)
        
        # 获取当前价格
        price_info = await trading_system.client._send_request(
            method="ticker.price",
            params={"symbol": symbol}
        )
        current_price = Decimal(price_info['price'])
        
        # 下一个低于市价20%的买单（不会立即成交）
        order_price = current_price * Decimal('0.8')
        quantity = Decimal('0.001')  # 最小数量
        
        logger.info("当前价格: %s", current_price)
        logger.info("下单价格: %s", order_price)
        logger.info("下单数量: %s", quantity)
        
        order = await trading_system.place_order(
            symbol=symbol,
            side="BUY",
            order_type="LIMIT",
            quantity=quantity,
            price=order_price
        )
        logger.info("订单信息: %s", order)
        
        # 4. 测试查询订单
        logger.info("4. 测试查询活跃订单...")
        logger.info("活跃订单: %s", trading_system.active_orders)
        
        # 5. 测试取消订单
        if order and 'orderId' in order:
            logger.info("5. 测试取消订单...")
            cancel_result = await trading_system.cancel_order(
                symbol=symbol,
                order_id=order['orderId']
            )
            logger.info("取消结果: %s", cancel_result)
        
        logger.info("测试完成 ✅")
        
    except Exception as e:
        logger.error("测试失败: %s", str(e))
        raise
    finally:
        # 确保关闭连接
        if trading_system and trading_system.client:
            await trading_system.client.close()

async def main():
    """主函数"""
    try:
        await test_trading_system()
    except KeyboardInterrupt:
        logger.info("程序终止")
    except Exception as e:
        logger.error("程序错误: %s", str(e))
        raise

if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main()) 