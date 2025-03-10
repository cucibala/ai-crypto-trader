import unittest
import os
import sys
from pathlib import Path
import asyncio
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.settings import MODEL_CONFIG

class TestLLMConfig(unittest.TestCase):
    """测试大模型配置"""

    def setUp(self):
        """测试前的设置"""
        self.openai_config = MODEL_CONFIG['openai']
        self.anthropic_config = MODEL_CONFIG['anthropic']
        self.google_config = MODEL_CONFIG['google']
        self.proxy_config = MODEL_CONFIG['proxy']

    def test_openai_config_loading(self):
        """测试OpenAI配置加载"""
        self.assertIsNotNone(self.openai_config['api_key'], "OpenAI API密钥未设置")
        self.assertEqual(self.openai_config['model'], os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'))
        self.assertEqual(float(self.openai_config['temperature']), float(os.getenv('OPENAI_TEMPERATURE', '0.7')))
        self.assertEqual(int(self.openai_config['max_tokens']), int(os.getenv('OPENAI_MAX_TOKENS', '2000')))

    def test_openai_api_connection(self):
        """测试OpenAI API连接"""
        try:
            # 配置OpenAI客户端
            base_url = self.openai_config['base_url'] if self.openai_config['base_url'] else "https://api.openai.com/v1"
            client = OpenAI(
                api_key=self.openai_config['api_key'],
                base_url=base_url,
                organization=self.openai_config['org_id'] if self.openai_config['org_id'] else None
            )

            # 测试API调用
            response = client.chat.completions.create(
                model=self.openai_config['model'],
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ],
                temperature=self.openai_config['temperature'],
                max_tokens=10
            )
            
            self.assertIsNotNone(response.choices[0].message.content)
            print("OpenAI测试响应:", response.choices[0].message.content)
            
        except Exception as e:
            self.fail(f"OpenAI API连接测试失败: {str(e)}")

    def test_anthropic_config_loading(self):
        """测试Anthropic配置加载"""
        if self.anthropic_config['api_key']:
            self.assertEqual(self.anthropic_config['model'], os.getenv('ANTHROPIC_MODEL', 'claude-3-opus'))

    def test_anthropic_api_connection(self):
        """测试Anthropic API连接"""
        if not self.anthropic_config['api_key']:
            self.skipTest("Anthropic API密钥未配置")
            
        try:
            client = Anthropic(api_key=self.anthropic_config['api_key'])
            
            response = client.messages.create(
                model=self.anthropic_config['model'],
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello, this is a test message."}
                ]
            )
            
            self.assertIsNotNone(response.content)
            print("Anthropic测试响应:", response.content)
            
        except Exception as e:
            self.fail(f"Anthropic API连接测试失败: {str(e)}")

    def test_google_config_loading(self):
        """测试Google AI配置加载"""
        if self.google_config['api_key']:
            self.assertEqual(self.google_config['model'], os.getenv('GOOGLE_AI_MODEL', 'gemini-pro'))

    def test_google_api_connection(self):
        """测试Google AI API连接"""
        if not self.google_config['api_key']:
            self.skipTest("Google AI API密钥未配置")
            
        try:
            genai.configure(api_key=self.google_config['api_key'])
            model = genai.GenerativeModel(self.google_config['model'])
            
            response = model.generate_content("Hello, this is a test message.")
            
            self.assertIsNotNone(response.text)
            print("Google AI测试响应:", response.text)
            
        except Exception as e:
            self.fail(f"Google AI API连接测试失败: {str(e)}")

    def test_proxy_config_loading(self):
        """测试代理配置加载"""
        if self.proxy_config['url']:
            self.assertIsNotNone(self.proxy_config['key'], "代理URL已设置但未提供密钥")

def async_test(coro):
    """装饰器：运行异步测试"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

if __name__ == '__main__':
    # 设置详细的测试输出
    unittest.main(verbosity=2) 