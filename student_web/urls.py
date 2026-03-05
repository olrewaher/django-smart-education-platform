from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from SecurityApp.forms import StudentLoginForm
# ==============================================================================
# 🎓 学生端路由模块 (Student Web URLs)
# ==============================================================================

urlpatterns = [
    # --------------------------------------------------------------------------
    # 1. 页面路由 (Page Routes)
    # --------------------------------------------------------------------------
    path('', views.index, name='index'),  # 首页

    # 🔐 认证相关 (使用 Django 内置视图，但指定自定义模板)
    path('login/', auth_views.LoginView.as_view(
        template_name='student_web/login.html',
        authentication_form=StudentLoginForm  # <--- 加上这一句！
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),  # 个人中心

    # 📚 课程详情路由
    # 场景A: 默认进入课程页 (自动播放第1集)
    path('case/<int:case_id>/', views.case_detail, name='case_detail'),
    # 场景B: 点击右侧目录，播放指定第N集
    path('case/<int:case_id>/chapter/<int:chapter_id>/', views.case_detail, name='case_chapter'),

    # --------------------------------------------------------------------------
    # 2. API 接口路由 (JSON API)
    #    供前端 Ajax/Fetch 调用，实现无刷新交互
    # --------------------------------------------------------------------------
    # 📝 笔记操作
    path('api/post-note/<int:case_id>/', views.api_post_note, name='api_post_note'),
    path('api/delete-note/<int:note_id>/', views.api_delete_note, name='api_delete_note'),

    # 💬 评论操作
    path('api/post-comment/<int:case_id>/', views.api_post_comment, name='api_post_comment'),
    path('api/delete-comment/<int:comment_id>/', views.api_delete_comment, name='api_delete_comment'),
    path('api/get-comments/<int:case_id>/', views.api_get_comments, name='api_get_comments'),

    # ⭐ 收藏操作 (🔥 核心修复：修正了 URL 路径，与前端 fetch 保持一致)
    path('api/toggle-favorite/<int:case_id>/', views.api_toggle_favorite, name='api_toggle_favorite'),

    # 📊 数据统计
    path('api/active-users/', views.get_active_users, name='api_active_users'),

    #👍点赞功能
    path('api/toggle-comment-like/<int:comment_id>/', views.toggle_comment_like, name='toggle_comment_like'),

    path('api/update-duration/', views.update_study_duration, name='update_study_duration'),

    #消息通知
    path('api/read-notifications/', views.api_read_notifications, name='read_notifications'),

    # 笔记导出
    path('export-notes/', views.export_notes, name='export_notes'),
    #个人中心自动打卡日历
    path('api/study-calendar/', views.api_get_study_calendar, name='api_study_calendar'),
]

