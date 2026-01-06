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


def product_detail_view(request, product_id):
    """Product detail page view"""
    try:
        product = Product.objects.select_related('product_category').get(id=product_id, is_active=True)
        
        # Get related products (same category, excluding current product)
        related_products = Product.objects.filter(
            is_active=True,
            product_category=product.product_category
        ).exclude(id=product.id)[:4]
        
        # If not enough related products, get any active products
        if related_products.count() < 4:
            additional = Product.objects.filter(is_active=True).exclude(id=product.id)[:4-related_products.count()]
            related_products = list(related_products) + list(additional)
        
        context = {
            'product': product,
            'related_products': related_products,
        }
        return render(request, 'home/product_detail.html', context)
    except Product.DoesNotExist:
        from django.http import Http404
        raise Http404("Product not found")


def cart_view(request):
    """Cart page view"""
    return render(request, 'home/cart.html')


def checkout_view(request):
    """Checkout page view"""
    # Redirect to login if not authenticated
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(f"{reverse('account:signin')}?next={reverse('home:checkout')}")
    return render(request, 'home/checkout.html')


def billing_view(request):
    """Billing page view"""
    # Redirect to login if not authenticated
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(f"{reverse('account:signin')}?next={reverse('home:billing')}")
    return render(request, 'home/billing.html')


def order_confirmation_view(request, order_id):
    """Order confirmation page view"""
    from .models import Order
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        context = {
            'order': order,
        }
        return render(request, 'home/order_confirmation.html', context)
    except Order.DoesNotExist:
        from django.http import Http404
        raise Http404("Order not found")


def my_orders_view(request):
    """My Orders page view"""
    if not request.user.is_authenticated:
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect(f"{reverse('account:signin')}?next={reverse('home:my-orders')}")
    
    from .models import Order
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'home/my_orders.html', context)
