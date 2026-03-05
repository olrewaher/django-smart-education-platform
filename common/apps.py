from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"

    # 🔥 核心修改：设置 App 的中文显示名称
    # 这解决了左侧菜单显示 "Common" 的问题
    verbose_name = "教学资源管理"