#-*-coding:utf-8-*-
from django.contrib import admin
from django.urls import path
from user.views import RegisterView, LoginView, ActiveView, LoginoutView, UserInfoView, UserOrderView, UserSiteView
from order.views import OrderPayView, CheckPayView

app_name = 'user'
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('active/str<token>/', ActiveView.as_view(), name='active'),
    path('logout/', LoginoutView.as_view(), name='logout'),

    path('', UserInfoView.as_view(), name='user'),
    path('order/int<page>/', UserOrderView.as_view(), name='order'),
    path('address/', UserSiteView.as_view(), name='address'),
    path('pay/', OrderPayView.as_view(), name='pay'),
    path('check/', CheckPayView.as_view(), name='check')
]
