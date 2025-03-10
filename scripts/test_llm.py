#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import unittest
import asyncio

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_llm_config import TestLLMConfig, async_test

def run_tests():
    """运行所有LLM配置测试"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(TestLLMConfig('test_openai_config_loading'))
    suite.addTest(TestLLMConfig('test_anthropic_config_loading'))
    suite.addTest(TestLLMConfig('test_google_config_loading'))
    suite.addTest(TestLLMConfig('test_proxy_config_loading'))
    
    # 添加异步测试用例
    suite.addTest(async_test(TestLLMConfig('test_openai_api_connection')))
    suite.addTest(async_test(TestLLMConfig('test_anthropic_api_connection')))
    suite.addTest(TestLLMConfig('test_google_api_connection'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 