from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from products.models import Product, ProductCategory
import json

User = get_user_model()


def is_admin_or_superadmin(user):
    """Check if user is admin or superadmin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'user_type', None) in ['admin', 'superadmin'])


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def admin_dashboard(request):
    """Admin dashboard view"""
    return render(request, 'admin_panel/dashboard.html')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def admin_redirect(request):
    """Redirect to dashboard"""
    return redirect('admin_panel:dashboard')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def products_management(request):
    """Products management page"""
    return render(request, 'admin_panel/products.html')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def categories_management(request):
    """Categories management page"""
    return render(request, 'admin_panel/categories.html')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def orders_management(request):
    """Orders management page"""
    return render(request, 'admin_panel/orders.html')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def users_management(request):
    """Users management page"""
    return render(request, 'admin_panel/users.html')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def add_user(request):
    """Add user page"""
    context = {
        'action': 'add'
    }
    return render(request, 'admin_panel/user_form.html', context)


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def update_user(request, user_id):
    """Update user page"""
    try:
        user = User.objects.get(id=user_id)
        context = {
            'user_obj': user,
            'action': 'update'
        }
        return render(request, 'admin_panel/user_form.html', context)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('admin_panel:users')


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def add_product(request):
    """Add product page"""
    categories = ProductCategory.objects.filter(is_active=True)
    context = {
        'categories': categories,
        'form_title': 'Add New Product',
        'is_edit': False
    }
    return render(request, 'admin_panel/product_form.html', context)


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def update_product(request, product_id):
    """Update product page"""
    product = get_object_or_404(Product, pk=product_id)
    categories = ProductCategory.objects.filter(is_active=True)
    
    product_data = {
        'id': str(product.id),
        'code': product.code or '',
        'name': product.name,
        'description': product.description or '',
        'cost': product.cost,
        'quantity': product.quantity,
        'img_url': product.img_url.url if product.img_url else '',
        'discount': product.discount or 0,
        'is_active': product.is_active,
        'product_category_id': str(product.product_category.id) if product.product_category else '',
    }

    context = {
        'categories': categories,
        'product': json.dumps(product_data),
        'form_title': f'Update Product: {product.name}',
        'is_edit': True
    }
    return render(request, 'admin_panel/product_form.html', context)


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def add_category(request):
    """Add category page"""
    context = {
        'action': 'add'
    }
    return render(request, 'admin_panel/category_form.html', context)


@user_passes_test(is_admin_or_superadmin, login_url='/account/signin/')
def update_category(request, category_id):
    """Update category page"""
    category = get_object_or_404(ProductCategory, pk=category_id)
    context = {
        'category': category,
        'action': 'update'
    }
    return render(request, 'admin_panel/category_form.html', context)

