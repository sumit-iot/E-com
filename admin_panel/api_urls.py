from django.urls import path
from . import views_api

app_name = 'admin_api'

urlpatterns = [
    path('dashboard-stats/', views_api.dashboard_stats, name='dashboard-stats'),
    path('users/', views_api.admin_users_list, name='users'),
    path('users/<int:user_id>/', views_api.get_user, name='user-detail'),
    path('users/create/', views_api.create_user, name='user-create'),
    path('users/<int:user_id>/update/', views_api.update_user_api, name='user-update'),
    path('users/<int:user_id>/delete/', views_api.delete_user, name='user-delete'),
    path('categories/', views_api.admin_categories_list, name='categories'),
    path('categories/<uuid:category_id>/', views_api.get_category, name='category-detail'),
    path('categories/create/', views_api.AdminCategoryCreateAPIView.as_view(), name='category-create'),
    path('categories/<uuid:category_id>/update/', views_api.AdminCategoryUpdateAPIView.as_view(), name='category-update'),
    path('categories/<uuid:category_id>/delete/', views_api.delete_category, name='category-delete'),
    path('products/', views_api.admin_products_list, name='products'),
    path('products/<uuid:product_id>/', views_api.get_product, name='product-detail'),
    path('products/create/', views_api.AdminProductCreateAPIView.as_view(), name='product-create'),
    path('products/<uuid:product_id>/update/', views_api.AdminProductUpdateAPIView.as_view(), name='product-update'),
    path('products/<uuid:product_id>/delete/', views_api.delete_product, name='product-delete'),
    path('orders/', views_api.admin_orders_list, name='orders'),
    path('orders/<uuid:order_id>/', views_api.get_order, name='order-detail'),
    path('orders/<uuid:order_id>/update-status/', views_api.update_order_status, name='order-update-status'),
    path('return-requests/', views_api.admin_return_requests_list, name='return-requests'),
    path('return-requests/<uuid:return_request_id>/update-status/', views_api.update_return_request_status, name='return-request-update-status'),
    path('return-requests/<uuid:return_request_id>/process-refund/', views_api.process_refund, name='process-refund'),
]

