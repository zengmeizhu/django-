from django.db import models
from django. contrib.auth.models import AbstractUser
from db.base_model import BaseModel

# Create your models here.

class User(AbstractUser, BaseModel):
    """用户模型类"""

    class Meta:
        db_table = "df_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name


class AddressManager(models.Manager):
    def get_default_address(self, user):
        try:
            address = self.get(user=user, is_default=True)
        except Address.DoesNotExist:
            address = None
        return address


class Address(BaseModel):
    user = models.ForeignKey("User", verbose_name="用户ID", on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name="收件人")
    addr = models.CharField(max_length=128, verbose_name="收件人地址")
    zig_code = models.CharField(max_length=6, verbose_name="邮编")
    phone = models.CharField(max_length=11, verbose_name="电话号码")
    is_default = models.BooleanField(default=False, verbose_name="是否为默认地址")

    objects = AddressManager()

    class Meta:
        db_table = "df_address"
        verbose_name = "地址"
        verbose_name_plural = verbose_name
