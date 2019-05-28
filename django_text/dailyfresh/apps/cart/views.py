from django.shortcuts import render, reverse, redirect
from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection

from utils.mixin import LoginRequiredMixin
from goods.models import GoodsSKU

# Create your views here.

#/cart/add
#用ajax post请求
class CartAddView(View):
    def post(self, request):

        # 从前台接收加入购物车的商品id和商品的count
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'ret': 0, 'errmsg': '请先登录'})
        id = request.POST.get('good_id')
        count = request.POST.get('count')

        #校验数据
        if not all([id, count]):
            return JsonResponse({'ret': 1, 'errmsg': '数据不全'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'ret': 2, 'errmsg': '商品数量有误'})
        try:
            sku = GoodsSKU.objects.get(id=id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'ret': 3, 'errmsg': '该商品不存在'})

        # 将这些数据存入redis
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = conn.hget(cart_key, id)
        if cart_count:
            count += int(cart_count)
        if count > sku.stock:
            return JsonResponse({'ret': 4, 'errmsg': '库存不足'})
        conn.hset(cart_key, id, count)
        total_count = conn.hlen(cart_key)
        return JsonResponse({'ret': 5, 'total_count': total_count, 'msg': '添加成功'})


class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        #从redis 中取出购物车数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        #从redis获取所有购物车商品的id并从数据库中取出其sku
        cart_skus = conn.hgetall(cart_key)

        total_count = 0
        total_price = 0
        skus = []
        for sku_id, count in cart_skus.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            sku_price = sku.price * int(count)
            sku.sku_price = sku_price
            sku.sku_count = count
            skus.append(sku)
            total_count += int(count)
            total_price += sku_price
        #整理数据
        context = {'skus': skus,
                   'total_count': total_count,
                   'total_price': total_price

        }
        return render(request, 'cart.html', context)


class CartUpdateView(View):
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'ret': 0, 'errmsg': '请先登录'})
        id = request.POST.get('good_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([id, count]):
            return JsonResponse({'ret': 1, 'errmsg': '数据不全'})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'ret': 2, 'errmsg': '商品数量有误'})
        try:
            sku = GoodsSKU.objects.get(id=id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'ret': 3, 'errmsg': '商品不存在'})

        if count > sku.stock:
            return JsonResponse({'ret': 4, 'errmsg': '库存不足'})
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hset(cart_key, id, count)
        #计算用户购物车中商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        return JsonResponse({'ret': 5, 'total_count': total_count, 'msg': '更新成功'})



class CartDeleteView(View):
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'ret': 0, 'errmsg': '请先登录'})
        id = request.POST.get('good_id')
        #校验数据
        if not id:
            return JsonResponse({'ret': 1, 'errmsg': '无效的商品id'})
        try:
            sku = GoodsSKU.objects.get(id=id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'ret': 2, 'errmsg': '商品不存在'})
        #删除购物车中的数据
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        conn.hdel(cart_key, id)
        # 计算用户购物车中商品的总件数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)
        return JsonResponse({'ret': 3, 'total_count': total_count, 'msg': '删除成功'})








