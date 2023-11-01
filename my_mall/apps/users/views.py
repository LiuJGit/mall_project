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
from django.contrib.auth.mixins import LoginRequiredMixin

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

        # 登录，具体操作就是状态保持写session：在cookies中写一个sessionid，然后redis中也保存对应的session信息，表示该用户已登录。
        login(request, user)
        # 使用remembered确定状态保持周期（实现记住登录）
        if remembered != 'on':
            # 没有记住登录：状态保持在浏览器会话结束后就销毁
            request.session.set_expiry(0) # 单位是秒
        else:
            # 记住登录：状态保持周期为两周:默认是两周
            request.session.set_expiry(None)

        # 登录成功，响应结果:
        # (1) 请求的url**不含**{{ redirect_field_name }}参数，则重定向到首页；
        # (2) 请求的url**含有**{{ redirect_field_name }}参数，则重定向到该参数给出的地址；
        # 强调一下，可以看到，这里前端表单的action属性为空，因此表单提交时的目标地址默认为当前页面的URL。
        # 这里表单发送的是 POST 请求，但我们也可以通过 GET 获取 URL 中的参数。
        # {{ redirect_field_name }} 默认为 next.
        next = request.GET.get('next')
        if next:
            # 重定向到 next
            response = redirect(next)
        else:
            # 重定向到首页
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
    

# class UserInfoView(View):
#     """用户中心"""

#     def get(self,request):
#         """提供用户中心页面"""
#         # 查看request对象的所有属性和方法
#         print(dir(request))
#         # request.user是一个用户实例对象，虽然是从request dot，但并不是浏览器发过来的，而是
#         # django通过中间件'django.contrib.auth.middleware.AuthenticationMiddleware'生成的。
#         # 查看源码可知，django是通过请求cookies中的sessionid去redis里面查user，只要request.COOKIES中不存在sessionid或redis中不存在相应的记录，
#         # 都会返回一个AnonymousUser匿名用户对象，表示未登录。
#         logger.info(request.user)
#         logger.info(type(request.user))
#         logger.info(request.COOKIES)
#         logger.info(request.session)
#         if request.user.is_authenticated:
#             # 当用户登录后，才能访问用户中心。
#             return render(request, 'user_center_info.html')
#         else:
#             # 如果用户未登录，就不允许访问用户中心，将用户引导到登录界面。
#             return redirect(reverse('users:login'))
        

class UserInfoView(LoginRequiredMixin, View):
    """用户中心
    LoginRequiredMixin一定要放在View之前，因为这里是多继承，
    且存在同名的方法，涉及到的MRO（Method Resolution Order）的知识点
    """
    
    # login_url = '/login'
    # redirect_field_name = '_from' # redirect_field_name 默认值为 'next'
    """
    访问需登录授权才能访问的页面 A，比如这里的用户中心页面：
    (1) 已登录，则允许访问；
    (2) 未登录，则重定向到 "{{ login_url }}/?{{ redirect_field_name }}={{ url_A }}"，记为 B。
    这里我们借助模板语言给出了重定向的url，其中 {{ url_A }} 表示 A 的 url。

    也就是说，我们最开始想访问 A，但因为没有登录，所以跳转到 B，而 B 实际上就是登录页面，只不过采用get请求的方式
    拼接了参数 {{ redirect_field_name }}，其值为我们最开始想访问的 A 的 url。由此，对于这种情况，我们可以修改前
    面登录视图的逻辑：拿到get请求参数 {{ redirect_field_name }} 的值，在成功登录后重定向到我们最开始想访问的 A，
    而不是登录成功后统一重定向到index页面。整个过程就是：
    `访问A-->发现未登录,跳转到B -->登录成功,跳转回A`
    因此，redirect_field_name 默认取为 'next'，是表示登录成功后下一站的 url。这里我们也不妨令其为 '_from'，因为
    这也是我们跳转到登录页面前，想要访问的地址。 

    login_url 也可以在项目的配置文件中进行全局设置，只不过变量名要大写 LOGIN_URL。两处均设置时，这里 login_url 的
    优先级更高。此外，无论在哪里设置，均不能使用 reverse 函数，而必须直接给出路径，因为程序存在加载先后的问题，否则会报错。
    """
    
    def get(self,request):
        """提供用户中心页面"""
        return render(request, 'user_center_info.html')