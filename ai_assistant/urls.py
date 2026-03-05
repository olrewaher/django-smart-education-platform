from django.urls import path
from . import views

urlpatterns = [
    # 这里的 'chat/' 会和主路由拼接，变成前端请求的 /ai_assistant/chat/
    path('chat/', views.chat_api, name='chat_api'),
]