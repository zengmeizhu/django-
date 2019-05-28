from django.shortcuts import render, redirect, reverse
from django.views import View
from django_redis import get_redis_connection
from django.core.paginator import Paginator

from goods.models import GoodsType, GoodsSKU, GoodSPU, GoodSKUImage, IndexByTurns, IndexSales, IndexClass
from order.models import OrderGoods


# Create your views here.

class IndexView(View):
    def get(self, request):
        #获取商品种类
        goods_types = GoodsType.objects.all()
        #获取首页轮播商品
        goods_by_turns = IndexByTurns.objects.all().order_by('turns_index')
        #获取促销商品
        goods_sales = IndexSales.objects.all().order_by('sales_index')
        #获取首页分类展示商品
        for type in goods_types:
            goods_words = IndexClass.objects.filter(index_class=type, index_display_type=0).order_by('index_index')
            goods_pics = IndexClass.objects.filter(index_class=type, index_display_type=1).order_by('index_index')
            type.words = goods_words
            type.pics = goods_pics
        #获取购物车商品总数
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            cart_count = conn.hlen(cart_key)
        cart_count = 0

        #组织数据
        context = {'types': goods_types,
                   'turns': goods_by_turns,
                   'sales': goods_sales,
                   'cart_count': cart_count

        }
        return render(request, 'index.html', context)


class DetailView(View):
    def get(self, request, id):
        #获取商品详情
        try:
            sku = GoodsSKU.objects.get(id=id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))

        # 获取分类商品
        types = GoodsType.objects.all()
        #获取评论信息
        comment = OrderGoods.objects.filter(sku=sku).exclude(comment='')
        #获取新品
        new_goods = GoodsSKU.objects.fiter(type=sku.type).order_by('-create_time')[:2]
        #获取同一个spu的其他规格的商品
        same_spu = GoodSPU.objects.filter(spu=sku.spu).exclude(id=id)[:2]
        #获取购物车商品总数
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            cart_count = conn.hlen(cart_key)
            # 添加历史浏览记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            history_key = 'history_%d' % user.id
            #删除缓存中的该商品的浏览记录lrem(key, count, value) count 表示需要删除的记录的条数，count=0表示删除所有
            conn.lrem(history_key, 0, id)
            #添加该商品的浏览记录
            conn.lpush(history_key, id)
            #只保存用户最近浏览的5条信息
            conn.ltrim(history_key, 0, 4)


        #数据整合
        context = {'types': types,
                   'sku': sku,
                   'cart_count': cart_count,
                   'comment': comment,
                   'new_goods': new_goods,
                   'same_spu': same_spu

        }
        return render(request, 'detail.html', context)


#list/type_id/page?sort=
class ListView(View):
    def get(self, request, type_id, page):
        #校验数据
        try:
           type =  GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect(reverse('goods:index'))

        #获取所有种类
        types = GoodsType.objects.all()

        #获取新品信息
        new_goods = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        #根据接收的sort从数据库中找到数据
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'sales':
            skus = GoodsSKU.objects.filter(type=type).order_by('sales')
        else:
            sort = 'default'
            skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')

        #给数据分页并界定显示的页数范围
        try:
            page = int(page)
        except Exception as e:
            page = 1

        p = Paginator(skus, 1)
        page_to = p.page(page)
        sum_page = p.num_pages
        if page > sum_page:
            page = 1
        if sum_page < 5:
            ranges = p.page_range
        elif page < 3:
            ranges = range(1, 6)
        elif sum_page - page < 2:
            ranges = range(sum_page-4, sum_page+1)
        else:
            ranges = range(page-2, page+3)

        #获取购物车商品数目
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            cart_count = conn.hlen(cart_key)

        #整合数据
        context = {'page_to': page_to,
                   'type': type,
                   'types': types,
                   'sort': sort,
                   'new_goods': new_goods,
                   'cart_count': cart_count,
                   'ranges': ranges
        }

        return render(request, 'detail.html', context)









