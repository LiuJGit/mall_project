from django.shortcuts import render, redirect
from django.views import View
import re
from django import http
from users.models import User
from my_mall.utils.response_code import RETCODE
from django.db import DatabaseError
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
import logging

# Create your views here.


logger = logging.getLogger('django')

class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        """
        实现用户注册
        :param request: 请求对象
        :return: 注册结果
        """
        # 接收参数：表单参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')

        # 校验参数：前后端的校验需要分开，避免恶意用户越过前端逻辑发请求，要保证后端的安全，前后端的校验逻辑相同
        # 判断参数是否齐全:all([列表])：会去校验列表中的元素是否为空，只要有一个为空，返回false
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 判断用户名是否是5-20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        # 判断密码是否是8-20个数字
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')
        
        # 保存注册数据：是注册业务的核心
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg':'注册失败'})

        # 实现状态保持
        # Django用户认证系统提供了 login() 方法
        # 封装了写入session的操作，帮助我们快速实现状态保持
        login(request, user)

        # 响应结果：重定向到首页
        # return http.HttpResponse('注册成功，重定向到首页')
        # return redirect('/')
        # reverse('contents:index') == '/'
        response = redirect(reverse('contents:index'))
        # 在cookie中设置用户名，供vue读取，并在首页中显示，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response
    

class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})
    

class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})
    

class LoginView(View):
    """用户登录"""

    def get(self, request):
        """提供用户登录页面"""
        return render(request, 'login.html')

    def post(self, request):
        """实现用户登录逻辑"""
        # 接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 校验参数
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入正确的用户名或手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')

        # 认证用户:使用账号查询用户是否存在，如果用户存在，再校验密码是否正确，最后返回user对象。
        # 可以看到，上述过程完全可以自己实现而不调用authenticate。
        # 默认用户认证后端 AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']
        # 下面，我们在user.utils.py中自定义authentication backends，以实现多用户登录（用户名or手机号均能登录），
        # 并在项目setting中配置自定义后端：AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']。
        # 这样，from django.contrib.auth import authenticate 导入的 authenticate 就是我们自定义的 authenticate 方法。
        user = authenticate(username=username, password=password)
        if user is None:
            # 登录失败
            return render(request, 'login.html', {'account_errmsg': '账号或密码错误'})

        # 登录，具体操作就是状态保持写session，redis保存一些信息，里面什么内容可以先不用关注
        login(request, user)
        # 使用remembered确定状态保持周期（实现记住登录）
        if remembered != 'on':
            # 没有记住登录：状态保持在浏览器会话结束后就销毁
            request.session.set_expiry(0) # 单位是秒
        else:
            # 记住登录：状态保持周期为两周:默认是两周
            request.session.set_expiry(None)

        # 登录成功，响应结果:重定向到首页
        response = redirect(reverse('contents:index'))
        # 在cookie中设置用户名，供vue读取，并在首页中显示，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response
    

class LogoutView(View):
    """用户退出登录"""

    def get(self, request):
        """实现用户退出登录的逻辑"""
        # 登录是写session，那么登出就是清除状态保持信息
        # Django用户认证系统提供了logout()方法
        # 封装了清理session的操作，帮助我们快速实现登出一个用户
        logout(request)

        # 退出登录后重定向到首页
        response = redirect(reverse('contents:index'))

        # 删除cookies中的用户名，这样首页就不会显示用户名了
        response.delete_cookie('username')

        # 响应结果
        return response