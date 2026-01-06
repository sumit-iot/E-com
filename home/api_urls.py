from django.urls import path
from . import views_api

app_name = 'home_api'

urlpatterns = [
    # Cart APIs
    path('cart/', views_api.get_cart, name='get-cart'),
    path('cart/add/', views_api.add_to_cart, name='add-to-cart'),
    path('cart/items/<uuid:item_id>/', views_api.update_cart_item, name='update-cart-item'),
    path('cart/items/<uuid:item_id>/remove/', views_api.remove_cart_item, name='remove-cart-item'),
    path('cart/clear/', views_api.clear_cart, name='clear-cart'),
    
    # Order APIs
    path('orders/', views_api.get_orders, name='get-orders'),
    path('orders/create/', views_api.create_order, name='create-order'),
    path('orders/<uuid:order_id>/', views_api.get_order, name='get-order'),
    path('orders/<uuid:order_id>/status/', views_api.update_order_status, name='update-order-status'),
    
    # Razorpay Payment APIs
    path('payment/razorpay/create-order/', views_api.create_razorpay_order, name='create-razorpay-order'),
    path('payment/razorpay/verify/', views_api.verify_razorpay_payment, name='verify-razorpay-payment'),
    
    # Return Request APIs
    path('returns/create/', views_api.create_return_request, name='create-return-request'),
    path('returns/', views_api.get_return_requests, name='get-return-requests'),
]

