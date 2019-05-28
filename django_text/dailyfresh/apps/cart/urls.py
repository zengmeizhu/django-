#-*-coding:utf-8-*-
from django.contrib import admin
from django.urls import path
from cart.views import CartAddView, CartInfoView, CartUpdateView, CartDeleteView

app_name = 'cart'
urlpatterns = [
        path('add/', CartAddView.as_view(), name='add'),
        path('cart/', CartInfoView.as_view(), name='cart'),
        path('delete/', CartDeleteView.as_view(), name='delete'),
        path('update/', CartUpdateView.as_view(), name='update')

]