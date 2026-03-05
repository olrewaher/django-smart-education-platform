"""
主路由配置文件 (URL Configuration)
遵循企业级分发原则：主路由只负责应用分发，不处理具体业务。
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from SecurityApp import forms
from SecurityApp.forms import StudentLoginForm
urlpatterns = [
    # ==============================================================================
    # 1. 后台管理 (Admin System)
    # ==============================================================================
    path('admin/', admin.site.urls),

    # ==============================================================================
    # 2. 教师端子系统 (Teacher System)
    # ==============================================================================
    path('teacher/', include('teacher_system.urls')),

    # 🔥 升级：CKEditor 5 专用图片上传接口
    path("ckeditor5/", include('django_ckeditor_5.urls')),

    # 🔐 教师端专用找回密码 (红色主题通道)
    path('teacher/password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='admin/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             success_url='/teacher/password_reset/done/'
         ),
         name='admin_password_reset'),
    path('teacher/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='admin/password_reset_done.html'),
         name='admin_password_reset_done'),

    # ==============================================================================
    # 3. 核心业务：学生端 (Student Web)
    # ==============================================================================
path('accounts/login/', auth_views.LoginView.as_view(
        template_name='student_web/login.html', # 👈 确保这里指向你的登录页HTML
        authentication_form=StudentLoginForm     # 👈 这里指定：使用带验证码的新表单！
    ), name='login'),


    path('accounts/', include('django.contrib.auth.urls')),  # Django 内置认证 URL


    path('', include('student_web.urls')),                   # 接管所有前台页面

    # ==============================================================================
    # 4. 安全管理 (Security System)
    # ==============================================================================

    # 这里通常还有你自己的 app 的路由，比如：
    path('', include('SecurityApp.urls')),

    path('captcha/', include('captcha.urls')),               #本地验证码生成图片接口

    # ==============================================================================
    # 5. 注册 ai_assistant 的路由
    # ==============================================================================

    path('ai_assistant/', include('ai_assistant.urls')),
]

# 开发环境静态文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)