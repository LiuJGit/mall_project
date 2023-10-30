"""
开发环境配置
Django settings for my_mall project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path
import os,sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent # 因为我们更改了配置文件的位置，此时BASE_DIR就是项目文件夹而不是manage.py所在的文件夹了
# print(f'BASE_DIR：{BASE_DIR}')

# 追加导包路径，简化app的注册导入
sys.path.insert(0, os.path.join(BASE_DIR,'apps'))
# # 查看项目导包路径
# print('项目导包路径：',sys.path)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rk=++2#fll0k&ru5#j@jyr!w(z9ki(d2rs&^9p=)=+lq)%jc62'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 注册用户模块
    'users.apps.UsersConfig', # 也可以只写包名 'users'
    # 注册首页广告模块
    'contents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_mall.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',  # jinja2模板引擎
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            # 自定义Jinja2模板引擎环境
            'environment': 'my_mall.utils.jinja2_env.jinja2_environment',
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_mall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    # # 原始数据库配置
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }

    # 使用MySQL数据库
    'default': {
        'ENGINE': 'django.db.backends.mysql', # 数据库引擎
        'HOST': '192.168.228.3', # 数据库主机
        'PORT': 3306, # 数据库端口
        'USER': 'lj', # 数据库用户名
        'PASSWORD': '123456', # 数据库用户密码
        'NAME': 'mymall' # 数据库名字
    },
}


# 配置缓存
CACHES = {
    "default": { # 默认
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.228.3:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": { # session
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://192.168.228.3:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache" # 配置session保存在缓存中
SESSION_CACHE_ALIAS = "session" # 使用别名为'session'的缓存保存session数据


# 配置日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志的格式，设置了2种
        'verbose': {
            'format': '---%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s---'
        },
        'simple': {
            'format': '---%(levelname)s %(module)s %(lineno)d %(message)s---'
        },
    },
    'filters': {  # 日志过滤器
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方式，设置了2种
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple' # 输出为 sample 格式
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.dirname(BASE_DIR), 'logs/mall.log'),  # 日志文件的位置，写满一个文件后自动创建下一个文件
            'maxBytes': 1 * 1024 * 1024, # 每个日志文件的最大容量，1m
            'backupCount': 10, # 最多保存的日志文件的数量
            'formatter': 'verbose' # 输出为 verbose 格式
        },
    },
    'loggers': {  # 基于上面的配置，创建日志记录器
        'django': {  # 定义了一个名为django的日志器，该日志器的配置如下
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否将日志消息传播到更高级别的日志记录器
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

# # 日志器的使用：
# import logging
# # 1 先选择上述创建的名为 django 的日志记录器
# logger = logging.getLogger('django')
# # 2 再输出日志
# logger.debug('测试logging模块debug')
# logger.info('测试logging模块info')
# logger.error('测试logging模块error')


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'

# 配置静态文件加载路径
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 'django.conf.global_settings'中可以查看所有的全局默认设置

# 指定本项目用户模型类
# 'django.conf.global_settings'中可以查看默认设置，AUTH_USER_MODEL = 'auth.User'
# 修改为自定义的模型类，AUTH_USER_MODEL = '应用名.模型类名'
AUTH_USER_MODEL = 'users.User'

# 指定自定义的用户认证后端
AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']