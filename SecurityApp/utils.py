# utils.py
from django.core.cache import cache
from django.conf import settings

# 定义一个固定的 Key，防止写错
CAPTCHA_CONFIG_KEY = "config:enable_saas_captcha"


def get_captcha_mode():
    """
    获取当前验证码模式
    返回: True (Cloudflare), False (本地)
    """
    # 尝试从数据库缓存里读取
    mode = cache.get(CAPTCHA_CONFIG_KEY)

    # 如果缓存里没存（比如第一次运行），默认使用 settings 里的配置
    if mode is None:
        return getattr(settings, 'ENABLE_SAAS_CAPTCHA', True)

    return mode


def set_captcha_mode(enable):
    """
    修改验证码模式
    timeout=None 表示永不过期（重启服务器后依然有效）
    """
    cache.set(CAPTCHA_CONFIG_KEY, enable, timeout=None)