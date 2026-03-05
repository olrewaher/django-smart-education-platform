# test_ai.py
from django.test import TestCase
from ai_assistant.utils import intent_router


class AIAssistantTestCase(TestCase):
    def test_intent_router_blacklist(self):
        """测试用例：测试 AI 意图拦截器的黑名单过滤功能"""
        # 1. 模拟正常学习提问
        valid_input = "请问这段 Python 爬虫代码是什么意思？"
        self.assertEqual(intent_router(valid_input), "PROCEED")

        # 2. 模拟违规/闲聊提问 (触发黑名单：游戏)
        invalid_input = "你能给我推荐几个好玩的游戏吗？"
        self.assertEqual(intent_router(invalid_input), "REFUSE")

        # 3. 模拟过短的无效输入
        short_input = "啊"
        self.assertEqual(intent_router(short_input), "REFUSE")

        print("✅ 测试通过：AI 意图网关前置拦截逻辑正常。")