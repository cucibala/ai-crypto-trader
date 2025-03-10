#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.binance_client import BinanceClient
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_market_data(client: BinanceClient):
    """测试市场数据"""
    try:
        symbol = 'BTCUSDT'
        
        # 1. 获取交易对价格
        logger.info("\n1. 获取交易对价格...")
        price_info = await client._send_request(
            method="ticker.price",
            params={"symbol": symbol}
        )
        logger.info(f"{symbol}当前价格: {price_info['price']}")
        
        # 2. 获取24小时价格统计
        logger.info("\n2. 获取24小时价格统计...")
        ticker_info = await client._send_request(
            method="ticker.24hr",
            params={"symbol": symbol}
        )
        logger.info(f"{symbol} 24小时统计:")
        logger.info(f"最高价: {ticker_info['highPrice']}")
        logger.info(f"最低价: {ticker_info['lowPrice']}")
        logger.info(f"成交量: {ticker_info['volume']}")
        logger.info(f"涨跌幅: {ticker_info['priceChangePercent']}%")
        
        # 3. 获取最新K线数据
        logger.info("\n3. 获取最新K线数据...")
        kline_info = await client._send_request(
            method="klines",
            params={
                "symbol": symbol,
                "interval": "1m",
                "limit": 1
            }
        )
        if kline_info and len(kline_info) > 0:
            k = kline_info[0]
            logger.info(f"{symbol} 最新1分钟K线:")
            logger.info(f"开盘价: {k[1]}")
            logger.info(f"最高价: {k[2]}")
            logger.info(f"最低价: {k[3]}")
            logger.info(f"收盘价: {k[4]}")
            logger.info(f"成交量: {k[5]}")
        
    except Exception as e:
        logger.error(f"市场数据测试失败: {str(e)}")
        raise

async def test_account_data(client: BinanceClient):
    """测试账户数据"""
    try:
        # 1. 获取账户信息
        logger.info("\n1. 获取账户信息...")
        timestamp = int(datetime.now().timestamp() * 1000)
        params = {
            "apiKey": BINANCE_API_KEY,
            "timestamp": timestamp
        }
        params["signature"] = client.generate_signature(params)
        
        account_info = await client._send_request(
            method="account.status",
            params=params
        )
        
        # 验证账户状态
        if account_info.get('accountType') != 'SPOT':
            logger.warning("非现货账户！")
            
        # 显示账户权限
        permissions = account_info.get('permissions', [])
        logger.info(f"账户权限: {permissions}")
        
        # 显示账户佣金费率
        commission_rates = account_info.get('commissionRates', {})
        logger.info("\n账户佣金费率:")
        logger.info(f"Maker费率: {commission_rates.get('maker', 'N/A')}")
        logger.info(f"Taker费率: {commission_rates.get('taker', 'N/A')}")
        
        # 显示账户余额
        balances = account_info.get('balances', [])
        non_zero_balances = [
            balance for balance in balances
            if Decimal(balance['free']) > 0 or Decimal(balance['locked']) > 0
        ]
        
        logger.info("\n账户余额:")
        for balance in non_zero_balances:
            logger.info(f"{balance['asset']}: "
                       f"可用={balance['free']}, "
                       f"冻结={balance['locked']}")
        
    except Exception as e:
        logger.error(f"账户数据测试失败: {str(e)}")
        raise

async def main():
    """主函数"""
    try:
        # 创建客户端
        client = BinanceClient()
        
        try:
            # 1. 测试市场数据
            logger.info("开始测试市场数据...")
            await test_market_data(client)
            
            # 2. 测试账户数据
            if BINANCE_API_KEY and BINANCE_API_SECRET:
                logger.info("\n开始测试账户数据...")
                await test_account_data(client)
            else:
                logger.warning("\nAPI密钥未配置，跳过账户数据测试")
            
            logger.info("\n测试完成 ✅")
            
        finally:
            # 确保关闭连接
            await client.close()
            
    except KeyboardInterrupt:
        logger.info("程序终止")
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise

if __name__ == '__main__':
    # 运行主函数
    asyncio.run(main()) 