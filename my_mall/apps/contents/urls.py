'''
新建contents子路由
'''
from django.conf.urls import url
from . import views

app_name = 'contents'
urlpatterns = [
    # 首页广告: '/'
    url(r'^$', views.IndexView.as_view(), name='index'),
]