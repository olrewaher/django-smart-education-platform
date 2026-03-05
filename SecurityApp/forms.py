from django import forms
from django.conf import settings
from captcha.fields import CaptchaField  # 本地库
from .fields import TurnstileField  # 我们刚才写的 SaaS 库
from django.contrib.auth.forms import AuthenticationForm # 引入Django自带登录表单
from .utils import get_captcha_mode     # 引入刚才写好的开关工具

class RegisterForm(forms.Form):
    username = forms.CharField(label="用户名", max_length=20)
    password = forms.CharField(label="密码", widget=forms.PasswordInput)

    # 预先定义两个字段，但在初始化时我们会删掉一个
    # 1. SaaS 验证字段
    saas_token = TurnstileField(required=False, label="安全验证")
    # 2. 本地验证字段
    local_captcha = CaptchaField(required=False, label="验证码")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 读取开关配置
        use_saas = getattr(settings, 'ENABLE_SAAS_CAPTCHA', True)

        if use_saas:
            # 模式 A: 使用 Cloudflare
            # 移除本地字段，保留 SaaS 字段并设为必填
            if 'local_captcha' in self.fields:
                del self.fields['local_captcha']
            self.fields['saas_token'].required = True
        else:
            # 模式 B: 使用本地图片降级
            # 移除 SaaS 字段，保留本地字段并设为必填
            if 'saas_token' in self.fields:
                del self.fields['saas_token']
            self.fields['local_captcha'].required = True


# ==============================================================================
# 新增：学生登录表单 (StudentLoginForm)
# ==============================================================================
class StudentLoginForm(AuthenticationForm):
    """
    继承自 Django 原生 AuthenticationForm
    功能：自动验证用户名密码 + 双模验证码
    """
    # 预先定义两个验证字段
    saas_token = TurnstileField(label="安全验证", required=False)
    local_captcha = CaptchaField(label="验证码", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 1. 美化输入框 (和你的UI风格保持一致)
        for field_name in ['username', 'password']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': '请输入学号' if field_name == 'username' else '请输入密码'
                })

        # 2. 读取动态开关 (使用 utils.py 里的工具)
        use_saas = get_captcha_mode()

        if use_saas:
            # === 模式 A: Cloudflare ===
            if 'local_captcha' in self.fields:
                del self.fields['local_captcha']
            self.fields['saas_token'].required = True
        else:
            # === 模式 B: 本地验证码 ===
            if 'saas_token' in self.fields:
                del self.fields['saas_token']
            self.fields['local_captcha'].required = True

            # 本地验证码样式优化
            self.fields['local_captcha'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': '请输入右侧字符',
                'style': 'width: 60%; display: inline-block; vertical-align: middle;'
            })