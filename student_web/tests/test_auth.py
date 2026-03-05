from django.test import TestCase, Client
from django.contrib.auth.models import User


class AuthenticationTestCase(TestCase):
    def setUp(self):
        # 预置条件：初始化测试客户端
        self.client = Client()

    def test_user_registration(self):
        """测试用例 1：测试新用户注册的核心逻辑"""
        # 模拟创建新用户
        user = User.objects.create_user(username='test_student', password='SecurePassword123!')

        # 断言：数据库里的用户总数必须为 1，且用户名匹配
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.username, 'test_student')
        print("✅ 测试通过：用户注册模块数据落库正常。")

    def test_user_login(self):
        """测试用例 2：测试用户登录鉴权逻辑"""
        # 预先在数据库造一个用户
        User.objects.create_user(username='login_user', password='testpassword')

        # 模拟前端发送登录请求
        login_success = self.client.login(username='login_user', password='testpassword')
        login_failed = self.client.login(username='login_user', password='wrongpassword')

        # 断言：密码正确时允许登录，密码错误时拒绝登录
        self.assertTrue(login_success)
        self.assertFalse(login_failed)
        print("✅ 测试通过：用户登录鉴权与 Session 签发逻辑正常。")