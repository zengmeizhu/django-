from django.shortcuts import render, reverse, redirect
from django.views import View
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django_redis import get_redis_connection
from django.core.paginator import Paginator

from user.models import User, Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from celery_tasks.tasks import send_active_mail
from utils.mixin import LoginRequiredMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
import re

# Create your views here.


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        #接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')#如果选中了则会等于on
        #校验数据
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        ret = re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email)
        if ret is None:
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        #校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        else:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        #将数据存入数据库
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        #发邮件
        my_email = 'z15279104901@126.com'
        ser = Serializer(settings.SECRET_KEY, 3600)
        info = {'comfirm': user.id}
        token = ser.dumps(info)
        token = token.decode()
        send_active_mail(email, token, username)

        return redirect(reverse('user:login'))


class ActiveView(View):
    def get(self, request, token):
        ser = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = ser.loads(token)
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
        except SignatureExpired as err:
            return HttpResponse('链接已过期')
        else:
            return redirect(reverse('user:login'))


class LoginView(View):
    def get(self, request):
        #如果没有这个判断，直接取username可能出现keyerror的错误
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        #接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')
        #校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        if user.is_active == 0:
            return redirect(reverse('user:register'), {'errmsg': '账户未激活'})
        login(request, user)
        #获取登陆后需要跳转到的地址，如果为空，则其默认为‘goods:index'
        next_url = request.GET.get('next', reverse('goods:index'))
        response = redirect(next_url)
        if remember == 'on':
            response.set_cookie({'username': username}, max_age=7*24*3600)
        else:
            response.delete_cookie('username')
        return response


class LoginoutView(View):
    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        conn = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        sku_ids = conn.lrange(history_key, 0, 4)#得到一个列表
        skus = []
        for sku_id in sku_ids:
            goods = GoodsSKU.objects.get(id=sku_id)
            skus.append(goods)
        context = {'address': address,
                   'goods': skus,
                   'page': 'user'
        }
        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin, View):
    def get(self, request, page):
        user = request.user
        order_list = OrderInfo.objects.filter(user=user).order_by('-create_time')

        for order in order_list:
            skus = OrderGoods.objects.filter(order=order).order_by('-create_time')

            for sku in skus:
                amount = sku.price * sku.count
                sku.amount = amount

            order.status_name = OrderInfo.ORDER_STATUS[order.status]
            order.skus = skus
        # 给数据分页并界定显示的页数范围
        try:
            page = int(page)
        except Exception as e:
            page = 1

        p = Paginator(order_list, 1)
        page_to = p.page(page)
        sum_page = p.num_pages
        if page > sum_page:
            page = 1
        if sum_page < 5:
            ranges = p.page_range
        elif page < 3:
            ranges = range(1, 6)
        elif sum_page - page < 2:
            ranges = range(sum_page - 4, sum_page + 1)
        else:
            ranges = range(page - 2, page + 3)
        #整合数据
        context = {'page': 'order',
                   'ranges': ranges,
                   'page_to': page_to

        }
        return render(request, 'user_center_order.html', )


class UserSiteView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        address = Address.objects.get_default_address(user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': 'address'})

    def post(self, request):
        user = request.user
        receiver = request.POST.get('rec')
        address = request.POST.get('add')
        zip_code = request.POST.get('zip')
        phone = request.POST.get('pho')

        if not all([user, receiver, address, zip_code, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        ret = re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone)
        if not ret:
            return render(request, 'user_center_site.html', {'errmsg': '电话号码错误'})

        Address.objects.create_by(user=user,
                                  receiver=receiver,
                                  addr=address,
                                  zig_code=zip_code,
                                  phone=phone)
        default_address = Address.objects.get_default_address(user)
        if default_address:
            is_default = False
        else:
            is_default = True

        return redirect(reverse('user:address'))












