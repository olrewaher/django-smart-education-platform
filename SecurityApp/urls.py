
from django.contrib import admin
from django.urls import path, include  # 确保导入了 include
from . import views

urlpatterns = [
    # path('admin/', admin.site.urls),
    # 把这一行加到 urlpatterns 列表里
    # 这是为了让本地验证码能生成图片和刷新
    path('captcha/', include('captcha.urls')),
    path('switch/<str:mode>/', views.switch_captcha, name='switch_captcha'),
]