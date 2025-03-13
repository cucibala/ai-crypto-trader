import os
import asyncio
import logging
from binance.client import Client
from models.gpt_model import GPTModel
from trading.auto_trader import AutoTrader
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auto_trader.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    try:
        # 初始化币安客户端
        binance_client = Client(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET')
        )
        
        # 初始化 GPT 模型
        gpt_model = GPTModel(api_key=os.getenv('OPENAI_API_KEY'))
        
        # 创建并运行自动交易器
        trader = AutoTrader(binance_client, gpt_model)
        
        logger.info("自动交易系统启动...")
        await trader.run()
        
    except Exception as e:
        logger.error(f"自动交易系统运行错误: {str(e)}", exc_info=True)
        
if __name__ == "__main__":
    asyncio.run(main()) 