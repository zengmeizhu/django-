from django.contrib import admin
from django.urls import path
from order.views import PlaceOrderView, OrderCommitView

app_name = 'order'
urlpatterns = [
        path('place/', PlaceOrderView.as_view(), name='place'),
        path('commit/', OrderCommitView.as_view(), name='commit')
]