本项目是一个针对在线课程学习而设计开发的Web平台。


🛠️ 技术栈 (Tech Stack)
后端框架：Python 3.10 / Django 5.2

前端框架：Vue.js 2.7.x / Bootstrap 5 / HTML5 / CSS3

数据库：MySQL 8.0.45 (生产环境) / SQLite3 (开发与原型阶段)

大模型驱动：接入火山引擎大语言模型 API，支持 SSE 流式传输

架构模式：B/S 架构，前后端混合组件化开发 (MVT + Vue Components)

✨ 核心功能模块 (Core Features)

👨‍🎓 学生学习端
沉浸式视频学习：支持流媒体播放，视频播放至关键节点可触发预设的“分支弹窗交互”，强制专注度检测。

无刷新随手笔记：基于 Vue.js 数据双向绑定与 Axios，支持在视频侧边栏实时记录笔记，无需刷新页面。

树状嵌套评论区：支持 UGC 内容生产，运用“楼中楼”机制构建群体知识共创社区。

AI 智能伴随式答疑：悬浮式 AI 助教，基于 RAG（检索增强生成）切片算法，结合当前案例上下文提供精准解答，拒绝闲聊与违规话题。


👩‍🏫 教师管理端
资源全生命周期管理：支持上传 Markdown 图文及视频资源，设置案例分类标签与封面。

交互锚点动态配置：可视化配置视频弹窗的触发时间（秒）、问题及解析反馈。

UGC 敏感词合规管控：内置 SecurityApp 敏感词过滤引擎（基于 DFA 算法），可对高风险言论进行前置拦截与人工封禁。

多维学情追踪看板：基于底层 10 秒心跳包（Heartbeat）机制，精准统计学生真实学习时长，生成班级学情画像。



🚀 本地运行与部署 (Quick Start)
1. 环境准备
请确保本机已安装 Python 3.8+ 及 MySQL 8.0 服务。

2. 克隆与依赖安装
# 1. 下载项目代码并进入根目录
cd your_project_name

# 2. 创建并激活虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Windows 用户使用 venv\Scripts\activate

# 3. 安装依赖包
pip install -r requirements.txt


3. 数据库配置
在 MySQL 中创建对应的数据库。
或可选择云服务器的mysql公网地址

修改项目 settings.py 中的 DATABASES 配置，填入你的 MySQL 账号密码。

执行数据迁移命令，生成数据表：
python manage.py makemigrations
python manage.py migrate

4. 启动项目
# 1. 创建超级管理员账号（用于登录教师管理端）
python manage.py createsuperuser

# 2. 启动开发服务器
python manage.py runserver
