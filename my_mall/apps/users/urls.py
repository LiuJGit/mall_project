'''
新建users子路由
'''
from django.conf.urls import url
from . import views

app_name = 'users'
urlpatterns = [
    # 用户注册: reverse(users:register) == '/register/'
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
]