#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import unittest
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_news_api import TestNewsAPI, async_test

async def setup_test():
    """设置测试环境"""
    test = TestNewsAPI()
    test.setUp()
    await test.asyncSetUp()
    return test

async def teardown_test(test):
    """清理测试环境"""
    await test.asyncTearDown()

async def run_tests():
    """运行所有新闻API测试"""
    # 创建测试实例
    test = await setup_test()
    
    try:
        # 运行测试
        await test.test_fetch_crypto_news()
        print("\n所有测试通过！")
        return True
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
        return False
    finally:
        # 清理
        await teardown_test(test)

if __name__ == '__main__':
    # 运行测试
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1) 