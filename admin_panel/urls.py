from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_redirect, name='redirect'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('products/', views.products_management, name='products'),
    path('products/add/', views.add_product, name='add-product'),
    path('products/<uuid:product_id>/update/', views.update_product, name='update-product'),
    path('categories/', views.categories_management, name='categories'),
    path('categories/add/', views.add_category, name='add-category'),
    path('categories/<uuid:category_id>/update/', views.update_category, name='update-category'),
    path('orders/', views.orders_management, name='orders'),
    path('users/', views.users_management, name='users'),
    path('users/add/', views.add_user, name='add-user'),
    path('users/<int:user_id>/update/', views.update_user, name='update-user'),
]

