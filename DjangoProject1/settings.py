"""
Django settings for DjangoProject1 project.
企业级配置文件 - 适配 SimpleUI + 稳健的路径配置 + CKEditor 5 现代化支持
"""

from pathlib import Path
import os
import sys

# ================================================= #
#                 1. 基础路径配置                   #
# ================================================= #
BASE_DIR = Path(__file__).resolve().parent.parent

# ================================================= #
#                 2. 核心安全配置                   #
# ================================================= #
SECRET_KEY = "django-insecure-p$thgyu#*a@#q*7t0ub*idv8hn588fy&!5aldo%-&1u(hahcb_"
DEBUG = True
ALLOWED_HOSTS = ['*']

# ================================================= #
#                 3. 应用注册 (Apps)                #
# ================================================= #
INSTALLED_APPS = [
    'simpleui',
    "django.contrib.admin",
    "django.contrib.auth",
    'django.contrib.contenttypes',
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'captcha',  # 本地验证码应用
    'SecurityApp', # 第三方验证码应用
    'ai_assistant', #agent助教

    # 🔥 升级：使用 CKEditor 5
    'django_ckeditor_5',

    # 本地应用
    'common.apps.CommonConfig',
    'student_web.apps.StudentWebConfig',
    'teacher_system.apps.TeacherSystemConfig',
]

# ================================================= #
#                 4. 中间件配置                     #
# ================================================= #
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "DjangoProject1.urls"

# ================================================= #
#                 5. 模板配置 (Templates)           #
# ================================================= #
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, 'templates'),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "DjangoProject1.wsgi.application"

# ================================================= #
#                 6. 数据库 (Database)              #
# ================================================= #
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# 落地后转换为 MySQL 的配置信息
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'zs_project_db',       # 刚才建的数据库名
#         'USER': 'root',    # 你的数据库用户名
#         'PASSWORD': 'zs123456',  # 你的数据库密码
#         'HOST': '127.0.0.1',          # 数据库主机地址
#         'PORT': '3306',               # 默认端口
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         }
#     }
# }

#  云服务器 MySQL 的配置信息
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zs_project_db',       # 刚才建的数据库名
        'USER': 'root',    # 你的数据库用户名
        'PASSWORD': 'zs123456',  # 你的数据库密码
        'HOST': '47.92.0.118',          # 数据库主机地址
        'PORT': '3306',               # 默认端口
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}



# ================================================= #
#                 7. 验证与国际化                   #
# ================================================= #
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# ================================================= #
#           8. 静态文件与媒体文件配置               #
# ================================================= #
STATIC_URL = "static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# 媒体文件（视频、图片、附件）存放根目录
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ================================================= #
#              9. SimpleUI 配置                     #
# ================================================= #
SIMPLEUI_HOME_INFO = False
SIMPLEUI_ANALYSIS = False
SIMPLEUI_STATIC_OFFLINE = True
SIMPLEUI_LOADING = False
SIMPLEUI_LOGO = 'https://cdn.bootcdn.net/ajax/libs/bootstrap-icons/1.10.3/icons/mortarboard-fill.svg'
SIMPLEUI_DEFAULT_THEME = 'admin.lte.css'

SIMPLEUI_CONFIG = {
    'system_keep': False,
    'menus': [
        {
            'name': '教学管理',
            'icon': 'fas fa-book-reader',
            'models': [
                {'name': '思政案例库', 'icon': 'fas fa-book-open', 'url': 'common/casestudy/'},
                {'name': '分类管理', 'icon': 'fas fa-tags', 'url': 'common/category/'},
                {'name': '视频交互节点', 'icon': 'fas fa-code-branch', 'url': 'common/branchnode/'}
            ]
        },
        {
            'name': '互动中心',
            'icon': 'fas fa-comments',
            'models': [
                {'name': '学生评论', 'icon': 'far fa-comment-dots', 'url': 'common/comment/'},
                {'name': '学习笔记', 'icon': 'fas fa-pen-fancy', 'url': 'common/note/'},
                {'name': '收藏记录', 'icon': 'fas fa-star', 'url': 'common/favorite/'}
            ]
        },
        {
            'name': '人员与权限',
            'icon': 'fas fa-users-cog',
            'models': [
                {'name': '用户与角色管理', 'icon': 'fas fa-user-edit', 'url': 'auth/user/'}
            ]
        },
        {
            'name': '数据可视化',
            'icon': 'fas fa-chart-pie',  # 图标，支持 FontAwesome
            'url': '/teacher/analytics/',  # 这里必须和你 teacher_system/urls.py 里配置的路径一致
            'breadcrumbs': ['首页', '数据可视化']
        }
    ]
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ================================================= #
#           11. 文件上传大小限制                     #
# ================================================= #
DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000

# ================================================= #
#           12. 🔥 CKEditor 5 现代化配置             #
# ================================================= #
# 定义文件存储（使用默认文件系统）
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', '|',
            'fontSize', 'fontColor', 'fontBackgroundColor', '|',
            'insertTable', 'mediaEmbed', 'removeFormat',
            'undo', 'redo'
        ],
        'theme': 'default',
        'image': {
            'toolbar': [
                'imageTextAlternative', 'imageStyle:inline',
                'imageStyle:block', 'imageStyle:side', '|',
                'toggleImageCaption', 'imageResize'
            ]
        },
        'table': {
            'contentToolbar': [ 'tableColumn', 'tableRow', 'mergeTableCells' ]
        },
        # 高度设置，确保编辑体验
        'height': 300,
        'width': 'auto',
        'language': 'zh-cn'
    }
}




# ==========================================
#           13. 企业级验证码配置中心          #
# ==========================================

# 1. 核心开关：True 使用 Cloudflare，False 降级为本地图片
# 在生产环境中，这个值通常读取环境变量，或者由 Nacos 动态下发
ENABLE_SAAS_CAPTCHA = False

# 2. Cloudflare Turnstile 配置 (去 Cloudflare官网申请)
TURNSTILE_SITE_KEY = ''      # 你的Site Key 公钥，给前端用
TURNSTILE_SECRET_KEY = ''  #你的Secret Key 私钥，给后端用

# 3. 本地验证码配置 (django-simple-captcha)
CAPTCHA_IMAGE_SIZE = (120, 40)
CAPTCHA_FONT_SIZE = 28


# 4 配置数据库缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table', # 这一行指定了数据库里的表名，叫什么都可以
    }
}

# ==========================================
#           14. AI Agent 智能助教配置          #
# ==========================================

#可接入其他第三方大模型的api
# 1. 你的火山引擎 API KEY (从火山引擎控制台获取)
VOLCENGINE_API_KEY = ""

# 2. 火山引擎的模型接入点 ID
VOLCENGINE_MODEL_EP = ""