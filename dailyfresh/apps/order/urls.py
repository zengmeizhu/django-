from django.contrib import admin
from django.urls import path
from order.views import PlaceOrderView, OrderCommitView, CommentView

app_name = 'order'
urlpatterns = [
        path('place/', PlaceOrderView.as_view(), name='place'),
        path('commit/', OrderCommitView.as_view(), name='commit'),
        path('comment/<int:order_id>', CommentView.as_view(), name='comment')
]