from django.urls import path
from . import views

# ==============================================================================
# 教师/管理端 API 路由配置
# ==============================================================================

urlpatterns = [
    # 1. 获取用户列表 (核心数据源)
    path('api/user-list/', views.get_user_list_api, name='api_user_list'),

    # 2. 封禁/解封操作
    path('api/user-action/', views.user_action_api, name='api_user_action'),

    # 3. 编辑用户 (改密、改名、改工号)
    path('api/user-edit/', views.edit_user_api, name='api_user_edit'),

    # 4. 新增用户 (创建账号+档案)
    path('api/user-add/', views.add_user_api, name='api_user_add'),

    #5.数据分析
    path('analytics/', views.case_analytics, name='case_analytics'),

]