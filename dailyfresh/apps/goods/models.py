from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField
# Create your models here.

class GoodsType(BaseModel):
    image = models.ImageField(upload_to="goods", verbose_name="种类图片")
    title = models.CharField(max_length=64, verbose_name="种类名称")
    logo = models.CharField(max_length=20, verbose_name="标识")

    class Meta:
        db_table = "df_goods_class"
        verbose_name = "商品种类"
        verbose_name_plural = verbose_name


class GoodSPU(BaseModel):
    spu_title = models.CharField(max_length=64, verbose_name="商品SPU名称")
    spu_detail = HTMLField(blank=True, verbose_name="商品SPU详情")

    class Meta:
        db_table = "df_good_spu"
        verbose_name = "商品spu"
        verbose_name_plural = verbose_name


class GoodsSKU(BaseModel):
    GOODSSKU_STATUS_CHOICE = (
        (1, "上架"),
        (0, "下架")
    )
    title = models.CharField(max_length=20, verbose_name="商品名称")
    type = models.ForeignKey("GoodsType", verbose_name="所属种类", on_delete=models.CASCADE)
    spu = models.ForeignKey("GoodSPU", verbose_name="所属SPU", on_delete=models.CASCADE)
    detail = models.CharField(max_length=256, verbose_name="商品简介")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品价格")
    unite = models.CharField(max_length=20, verbose_name="单位")
    status = models.SmallIntegerField(choices=GOODSSKU_STATUS_CHOICE, default=1, verbose_name="商品状态")
    image = models.ImageField(upload_to="goods", verbose_name="商品图片")
    stock = models.IntegerField(default=1, verbose_name="库存")
    sales = models.IntegerField(default=0, verbose_name="销量")

    class Meta:
        db_table = "df_good_sku"
        verbose_name = "商品sku"
        verbose_name_plural = verbose_name


class GoodSKUImage(BaseModel):
    goods_sku = models.ForeignKey("GoodsSKU", verbose_name="所属商品",on_delete=models.CASCADE)
    goods_image = models.ImageField(upload_to="goods", verbose_name="商品图片")

    class Meta:
        db_table = "df_good_sku_image"
        verbose_name = "商品图片"
        verbose_name_plural = verbose_name


class IndexByTurns(BaseModel):
    turns_sku = models.ForeignKey("GoodsSKU", verbose_name="所属商品SKU", on_delete=models.CASCADE)
    turns_image = models.ImageField(upload_to="goods", verbose_name="首页轮播商品图片")
    turns_index = models.SmallIntegerField(default=0,verbose_name="商品展示顺序")

    class Meta:
        db_table = "df_index_by_turns"
        verbose_name = "首页轮播商品"
        verbose_name_plural = verbose_name


class IndexSales(BaseModel):
    sales_title = models.CharField(max_length=20, verbose_name="活动名称")
    sales_image = models.ImageField(upload_to="goods", verbose_name="首页促销商品图片")
    sales_urls = models.URLField(verbose_name="活动链接")
    sales_index = models.SmallIntegerField(verbose_name="展示顺序")

    class Meta:
        db_table = "df_index_sales"
        verbose_name = "首页促销商品"
        verbose_name_plural = verbose_name


class IndexClass(BaseModel):
    DISPLAY_TYPE_CHOICES = (
        (0, "标题"),
        (1, "图片")
    )
    index_sku = models.ForeignKey("GoodsSKU", verbose_name="所属分类商品", on_delete=models.CASCADE)
    index_class = models.ForeignKey("GoodsType", verbose_name="商品所属分类", on_delete=models.CASCADE)
    index_display_type = models.SmallIntegerField(choices=DISPLAY_TYPE_CHOICES, default=1, verbose_name="展示类型")
    index_index = models.IntegerField(verbose_name="展示顺序")

    class Meta:
        db_table = "df_index_class"
        verbose_name = "首页分类商品展示"
        verbose_name_plural = verbose_name