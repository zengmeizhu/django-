from django.shortcuts import render, reverse, redirect
from django.views import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings

from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, OrderGoods
from utils.mixin import LoginRequiredMixin
from datetime import datetime
from alipay import Alipay
import os

# Create your views here.

class PlaceOrderView(LoginRequiredMixin, View):
    def post(self, request):
        """订单页面"""
        #接收参数
        user = request.user
        sku_ids = request.POST.getlist('sku_ids')
        #校验参数
        if not sku_ids:
            return redirect(reverse('cart:cart'))

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        total_price = 0
        total_count = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            count = conn.hget(cart_key, sku_id)
            amount = sku.price*count
            sku.count = count
            sku.amount = amount
            total_count += count
            total_price += amount
            skus.append(sku)
        #计算总金额
        transit_price = 10
        should_pay = total_price + transit_price
        #用户地址信息
        user_addr = Address.objects.filter(user=user)
        #整合参数
        sku_ids = ",".join(sku_ids)
        context = {'skus': skus,
                   'total_count': total_count,
                   'total_price': total_price,
                   'transit_price': transit_price,
                   'should_pay': should_pay,
                   'user_addr': user_addr,
                   'sku_ids': sku_ids

        }
        return render(request, 'place_order.html', context)


class OrderCommitView(View):
    @transaction.atomic
    def post(self, request):
        #接收参数
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'ret': 0, 'errmsg': '请先登录'})
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        #校验参数
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'ret': 1, 'errmsg': '数据不全'})
        if pay_method not in OrderInfo.PAY_METHOD_CHOICES.keys():
            return JsonResponse({'ret': 2, 'errmsg': '支付方式有误'})
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'ret': 3, 'errmsg': '地址有误'})

        total_price = 0
        total_count = 0

        transit_price = 10
        #设置保存点
        save_id = transaction.savepoint
        # 生成订单号
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        try:

            order = OrderInfo.create(order=order_id,
                                     user=user,
                                     address=addr,
                                     total_count=total_count,
                                     total_price=total_price,
                                     transit_price=transit_price,
                                     pay_method=pay_method

            )

            #生成订单商品
            sku_ids = sku_ids.split(',')
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id

            for sku_id in sku_ids:
                for i in range(3):
                    try:

                        sku = GoodsSKU.objects.get(id=sku_id)
                    except GoodsSKU.DoesNotExist:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'ret': 4, 'errmsg': '商品不存在'})
                    count = conn.hget(cart_key, sku_id)
                    if sku.store < count:
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'ret': 5, 'errmsg': '商品库存不足'})
                    # 更新商品销量和库存
                    orgin_store = sku.store
                    new_store = orgin_store - int(count)
                    new_sales = sku.sales + int(count)
                    res = GoodsSKU.objects.filter(id=sku_id, store=new_store).update(store=new_store, sales=new_sales)
                    if res == 0:
                        if i == 2:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'ret': 6, 'errmsg': '订单创建失败'})
                        continue
                    goods = OrderGoods.objects.create(order=order,
                                                      sku=sku,
                                                      count=count,
                                                      price=sku.price

                    )

                    #累计计算订单总价格和总数量
                    total_price += int(count) * sku.price
                    total_count += count
                    break
            #更新订单总价和总数量
            order.total_count = total_count
            order.total_price = total_price
            conn.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'ret': 6, 'msg': '订单创建失败'})
        return JsonResponse({'ret': 7, 'msg': '订单创建成功'})


class OrderPayView(View):
    def post(self, request):
        #判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'ret': 0, 'errmsg': '请先登陆'})

        #接收参数
        order_id = request.POST.get('order_id')
        #校验参数
        try:
            order = OrderInfo.objects.get(order=order_id)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'ret': 1, 'errmsg': '该订单不存在'})
        total_amount = order.total_price + order.transit_price
        #利用python_sdk调用支付宝的支付接口(1.初始化, 2.网站支付函数
        alipay = AliPay(
            appid="2016092900622396",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no="order_id",
            total_amount=total_amount,
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )

        pay_url = 'http://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'ret': 3, 'msg': '订单提交成功', 'pay_url': pay_url})


class CheckPayView(View):
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'ret': 0, 'errmsg': '请先登陆'})

        # 接收参数
        order_id = request.POST.get('order_id')
        # 校验参数
        try:
            order = OrderInfo.objects.get(order=order_id)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'ret': 1, 'errmsg': '该订单不存在'})
        total_amount = order.total_price + order.transit_price
        # 利用python_sdk调用支付宝的支付接口(1.初始化, 2.网站支付函数
        alipay = AliPay(

            appid="2016092900622396",
            app_notify_url=None,  # 默认回调url
            app_private_key_string=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=os.path.join(settings.BASE_DIR, 'apps/order/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True  # 默认False
        )
        #调用支付宝交易查询接口
        while True:
            response =  alipay.api_alipay_trade_query(order_id)
            if response.get('code') == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                #获取支付宝交易号
                trade_no = response.get('trade_no')
                #更新订单状态
                order.trade_on = trade_no
                order.status = 3
                order.save()
                #返回结果
                return JsonResponse({'ret': 3, 'msg': '支付成功'})
            elif response.get('code') == '40004' or (response.get('code') == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY'):
                import time
                time.sleep(3)
                continue
            else:
                return JsonResponse({'ret': 4, 'errmsg': '支付出错'})




