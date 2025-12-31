from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from products.models import Product, ProductCategory


def home_view(request):
    """Home page view"""
    return render(request, 'home/index.html')


def shop_view(request):
    """Shop page view with product listing"""
    # Get query parameters
    page = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    ordering = request.GET.get('ordering', '-created_on')
    page_size = request.GET.get('page_size', 16)
    
    # Get all active products
    products = Product.objects.filter(is_active=True).select_related('product_category')
    
    # Apply filters
    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search))
    
    if category:
        products = products.filter(product_category_id=category)
    
    if min_price:
        try:
            products = products.filter(cost__gte=int(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            products = products.filter(cost__lte=int(max_price))
        except ValueError:
            pass
    
    # Apply ordering
    products = products.order_by(ordering)
    
    # Pagination
    try:
        page_size = int(page_size)
    except ValueError:
        page_size = 16
    
    paginator = Paginator(products, page_size)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # Get all categories for filter dropdown
    categories = ProductCategory.objects.filter(is_active=True)
    
    # Calculate start and end indices for display
    start_index = page_obj.start_index() if hasattr(page_obj, 'start_index') else ((page_obj.number - 1) * page_size) + 1
    end_index = page_obj.end_index() if hasattr(page_obj, 'end_index') else min(page_obj.number * page_size, paginator.count)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'current_search': search,
        'current_category': category,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'current_ordering': ordering,
        'current_page_size': page_size,
    }
    
    return render(request, 'home/shop.html', context)


def return_policy_view(request):
    """Return Policy page view"""
    return render(request, 'home/return_policy.html')


def shipping_info_view(request):
    """Shipping Information page view"""
    return render(request, 'home/shipping_info.html')


def privacy_policy_view(request):
    """Privacy Policy with FAQ page view"""
    return render(request, 'home/privacy_policy.html')


def about_view(request):
    """About page view"""
    return render(request, 'home/about.html')


def contact_view(request):
    """Contact page view"""
    return render(request, 'home/contact.html')
