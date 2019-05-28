from django.db import models
from db.base_model import BaseModel


# Create your models here.

class OrderInfo(BaseModel):
    """订单模型"""
    PAY_METHOD_CHOICES = (
        (1, "支付宝"),
        (2, "微信支付"),
        (3, "银联支付"),
        (4, "货到付款")
    )

    ORDER_STATUS_CHOICES = (
        (1, "待发货"),
        (2, "待支付"),
        (3, "待收货"),
        (4, "待评价"),
        (5, "订单完成")
    )
    ORDER_STATUS = {
        1: "待发货",
        2: "待支付",
        3: "待收货",
        4: "待评价",
        5: "订单完成"
    }
    order = models.CharField(max_length=128, primary_key=True, verbose_name="订单编号")
    user = models.ForeignKey("user.User", verbose_name="用户", on_delete=models.CASCADE)
    address = models.ForeignKey("user.Address", verbose_name="用户地址", on_delete=models.CASCADE)
    total_count = models.IntegerField(default=1, verbose_name="商品总数")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品总价")
    transit_price = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="运费")
    pay_method = models.SmallIntegerField(choices=PAY_METHOD_CHOICES, default=1, verbose_name="支付方式")
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=1, verbose_name="订单状态")
    trade_on = models.CharField(max_length=128, default=0, verbose_name="支付编号")

    class Meta:
        db_table = "df_order_info"
        verbose_name = "订单"
        verbose_name_plural = verbose_name


class OrderGoods(BaseModel):
    """订单商品模型"""
    order = models.ForeignKey("OrderInfo", verbose_name="所属订单", on_delete=models.CASCADE)
    sku = models.ForeignKey("goods.GoodsSKU", verbose_name="商品", on_delete=models.CASCADE)
    count = models.IntegerField(default=1, verbose_name="数量")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品价格")
    comment = models.CharField(max_length=256, verbose_name="评论")

    class Meta:
        db_table = "df_order_goods"
        verbose_name = "订单商品"
        verbose_name_plural = verbose_name