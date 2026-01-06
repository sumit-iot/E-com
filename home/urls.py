from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='index'),
    path('shop/', views.shop_view, name='shop'),
    path('return-policy/', views.return_policy_view, name='return-policy'),
    path('shipping-info/', views.shipping_info_view, name='shipping-info'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy-policy'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('product/<uuid:product_id>/', views.product_detail_view, name='product-detail'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('billing/', views.billing_view, name='billing'),
    path('order/<uuid:order_id>/', views.order_confirmation_view, name='order-confirmation'),
    path('my-orders/', views.my_orders_view, name='my-orders'),
]

