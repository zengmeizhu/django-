#-*-coding:utf-8-*-
from django.contrib import admin
from django.urls import path
from goods.views import IndexView, DetailView, ListView

app_name = 'goods'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('detail/<int:id>/', DetailView.as_view(), name='detail'),
    path('list/<int:type_id>/<int:page>/', ListView.as_view(), name='list')
]