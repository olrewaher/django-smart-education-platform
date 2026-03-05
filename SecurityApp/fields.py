import requests
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

# 配置日志（企业级必备，方便排查问题）
logger = logging.getLogger(__name__)


class TurnstileField(forms.CharField):
    """
    SaaS 验证码字段：负责接收前端的 Token 并去 Cloudflare 核验
    """
    widget = forms.HiddenInput()  # 前端不需要输入框，只需要隐藏域存 Token

    def validate(self, value):
        super().validate(value)

        # 获取配置
        secret_key = getattr(settings, "TURNSTILE_SECRET_KEY", None)
        if not secret_key:
            logger.critical("Turnstile Secret Key 未配置！")
            raise ValidationError("系统配置错误，请联系管理员")

        try:
            # 发起 HTTP 请求进行核验
            # timeout=5 是关键：防止第三方挂了把我们也拖死（鲁棒性体现）
            response = requests.post(
                'https://challenges.cloudflare.com/turnstile/v0/siteverify',
                data={
                    'secret': secret_key,
                    'response': value,
                },
                timeout=5
            )
            result = response.json()
        except requests.RequestException as e:
            logger.error(f"Cloudflare 连接失败: {e}")
            # 这里可以选择抛出异常，或者在极端情况下默认通过（视业务安全等级而定）
            raise ValidationError("验证服务连接超时，请稍后重试")

        if not result.get('success'):
            logger.warning(f"验证失败，可能为机器人行为: {result}")
            raise ValidationError("安全验证失败，请刷新页面重试")