from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from products.models import ProductCategory, Product
from products.serializers import ProductCategorySerializer, ProductSerializer, ProductListSerializer

User = get_user_model()


def is_admin_or_superadmin(user):
    """Check if user is admin or superadmin"""
    if not user.is_authenticated:
        return False
    return (user.is_staff or 
            user.is_superuser or 
            getattr(user, 'user_type', None) in ['admin', 'superadmin'])


class IsAdminOrSuperAdmin(IsAuthenticated):
    """Permission class for admin or superadmin"""
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return is_admin_or_superadmin(request.user)


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        from products.models import Product
        from home.models import Order
        
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        total_users = User.objects.count()
        total_customers = User.objects.filter(user_type='common').count()
        
        # Calculate revenue from paid orders
        paid_orders = Order.objects.filter(payment_status='paid')
        revenue = sum(float(order.total) for order in paid_orders)
        
        return Response({
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'total_users': total_users,
            'total_customers': total_customers,
            'revenue': revenue,
            'total_earnings': revenue,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Error loading statistics: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def admin_users_list(request):
    """Get users list for admin panel"""
    try:
        search = request.query_params.get('search', '')
        user_type = request.query_params.get('user_type', 'all')
        
        users = User.objects.all()
        
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if user_type != 'all':
            users = users.filter(user_type=user_type)
        
        users_data = []
        for user in users:
            users_data.append({
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'user_type': getattr(user, 'user_type', 'common'),
                'mobile': getattr(user, 'mobile', '') or '',
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined.isoformat() if hasattr(user, 'date_joined') else None,
            })
        
        return Response({
            'users': users_data,
            'count': len(users_data)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error loading users: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def get_user(request, user_id):
    """Get single user by ID"""
    try:
        user = User.objects.get(id=user_id)
        return Response({
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'user_type': getattr(user, 'user_type', 'common'),
            'mobile': getattr(user, 'mobile', '') or '',
            'is_active': user.is_active,
            'is_staff': user.is_staff,
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error loading user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def create_user(request):
    """Create new user"""
    try:
        data = request.data.copy()
        
        # Validate required fields
        if not data.get('username'):
            return Response(
                {'error': 'Username is required', 'errors': {'username': ['This field is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not data.get('email'):
            return Response(
                {'error': 'Email is required', 'errors': {'email': ['This field is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not data.get('password'):
            return Response(
                {'error': 'Password is required', 'errors': {'password': ['This field is required.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if username or email already exists
        if User.objects.filter(username=data['username']).exists():
            return Response(
                {'error': 'Username already exists', 'errors': {'username': ['A user with this username already exists.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'Email already exists', 'errors': {'email': ['A user with this email already exists.']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )
        
        # Set additional fields
        if 'user_type' in data:
            user.user_type = data['user_type']
        if 'mobile' in data:
            user.mobile = data['mobile']
        if 'is_active' in data:
            user.is_active = data['is_active'] == 'true' or data['is_active'] is True
        if 'is_staff' in data:
            user.is_staff = data['is_staff'] == 'true' or data['is_staff'] is True
        if 'is_superuser' in data:
            user.is_superuser = data['is_superuser'] == 'true' or data['is_superuser'] is True
        if 'profile_img_url' in data:
            user.profile_img_url = data['profile_img_url']
        
        user.save()
        
        return Response({
            'message': 'User created successfully',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': f'Error creating user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminOrSuperAdmin])
def update_user_api(request, user_id):
    """Update user"""
    try:
        user = User.objects.get(id=user_id)
        data = request.data.copy()
        
        # Update fields
        if 'username' in data and data['username'] != user.username:
            if User.objects.filter(username=data['username']).exclude(id=user.id).exists():
                return Response(
                    {'error': 'Username already exists', 'errors': {'username': ['A user with this username already exists.']}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                return Response(
                    {'error': 'Email already exists', 'errors': {'email': ['A user with this email already exists.']}},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'user_type' in data:
            user.user_type = data['user_type']
        if 'mobile' in data:
            user.mobile = data['mobile']
        if 'is_active' in data:
            user.is_active = data['is_active'] == 'true' or data['is_active'] is True
        if 'is_staff' in data:
            user.is_staff = data['is_staff'] == 'true' or data['is_staff'] is True
        if 'is_superuser' in data:
            user.is_superuser = data['is_superuser'] == 'true' or data['is_superuser'] is True
        if 'profile_img_url' in data:
            user.profile_img_url = data['profile_img_url']
        
        user.save()
        
        return Response({
            'message': 'User updated successfully',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error updating user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAdminOrSuperAdmin])
def delete_user(request, user_id):
    """Delete user"""
    try:
        user = User.objects.get(id=user_id)
        # Don't allow deleting yourself
        if user.id == request.user.id:
            return Response(
                {'error': 'You cannot delete your own account'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.delete()
        return Response(
            {'message': 'User deleted successfully'},
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error deleting user: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def admin_categories_list(request):
    """Get categories list for admin panel"""
    try:
        search = request.query_params.get('search', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        
        categories = ProductCategory.objects.all().annotate(
            product_count=Count('product')
        ).order_by('category_name')
        
        if search:
            categories = categories.filter(category_name__icontains=search)
        
        # Manual pagination
        total = categories.count()
        start = (page - 1) * page_size
        end = start + page_size
        categories_page = categories[start:end]
        
        categories_data = []
        for category in categories_page:
            categories_data.append({
                'id': str(category.id),
                'category_name': category.category_name,
                'img_url': category.img_url.url if category.img_url else None,
                'discount': category.discount or 0,
                'is_active': category.is_active,
                'created_on': category.created_on.isoformat() if category.created_on else None,
                'product_count': category.product_count,
            })
        
        return Response({
            'categories': categories_data,
            'count': total,
            'page': page,
            'page_size': page_size,
            'num_pages': (total + page_size - 1) // page_size
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error loading categories: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def get_category(request, category_id):
    """Get single category by ID"""
    try:
        category = ProductCategory.objects.get(id=category_id)
        serializer = ProductCategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ProductCategory.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error loading category: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AdminCategoryCreateAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            data['created_by'] = request.user.username
            data['modified_by'] = request.user.username
            
            serializer = ProductCategorySerializer(data=data)
            if serializer.is_valid():
                category = serializer.save()
                return Response({
                    'message': 'Category created successfully',
                    'category': ProductCategorySerializer(category).data
                }, status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error creating category: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return Response(
                {'error': f'Error creating category: {str(e)}', 'traceback': error_traceback if settings.DEBUG else None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminCategoryUpdateAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, category_id, *args, **kwargs):
        try:
            category = ProductCategory.objects.get(id=category_id)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
            # If img_url is not in request.FILES (no new image uploaded), remove it from data to preserve existing image
            if 'img_url' not in request.FILES:
                data.pop('img_url', None)
            
            serializer = ProductCategorySerializer(category, data=data, partial=True)
            if serializer.is_valid():
                updated_category = serializer.save()
                return Response({
                    'message': 'Category updated successfully',
                    'category': ProductCategorySerializer(updated_category).data
                }, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ProductCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error updating category: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return Response(
                {'error': f'Error updating category: {str(e)}', 'traceback': error_traceback if settings.DEBUG else None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, category_id, *args, **kwargs):
        try:
            category = ProductCategory.objects.get(id=category_id)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
            # If img_url is not in request.FILES (no new image uploaded), remove it from data
            # Django will automatically preserve the existing image when the field is not provided
            if 'img_url' not in request.FILES:
                data.pop('img_url', None)
            
            serializer = ProductCategorySerializer(category, data=data)
            if serializer.is_valid():
                updated_category = serializer.save()
                return Response({
                    'message': 'Category updated successfully',
                    'category': ProductCategorySerializer(updated_category).data
                }, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ProductCategory.DoesNotExist:
            return Response(
                {'error': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error updating category: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return Response(
                {'error': f'Error updating category: {str(e)}', 'traceback': error_traceback if settings.DEBUG else None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['DELETE'])
@permission_classes([IsAdminOrSuperAdmin])
def delete_category(request, category_id):
    """Delete category"""
    try:
        category = ProductCategory.objects.get(id=category_id)
        category.delete()
        return Response(
            {'message': 'Category deleted successfully'},
            status=status.HTTP_200_OK
        )
    except ProductCategory.DoesNotExist:
        return Response(
            {'error': 'Category not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error deleting category: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def admin_products_list(request):
    """Get products list for admin panel"""
    try:
        search = request.query_params.get('search', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        
        products = Product.objects.all().select_related('product_category').order_by('-created_on')
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Manual pagination
        total = products.count()
        start = (page - 1) * page_size
        end = start + page_size
        products_page = products[start:end]
        
        serializer = ProductListSerializer(products_page, many=True)
        
        return Response({
            'results': serializer.data,
            'count': total,
            'page': page,
            'page_size': page_size,
            'num_pages': (total + page_size - 1) // page_size
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error loading products: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def get_product(request, product_id):
    """Get single product by ID"""
    try:
        product = Product.objects.get(id=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error loading product: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AdminProductCreateAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            data['created_by'] = request.user.username
            data['modified_by'] = request.user.username
            
            serializer = ProductSerializer(data=data)
            if serializer.is_valid():
                product = serializer.save()
                return Response({
                    'message': 'Product created successfully',
                    'product': ProductSerializer(product).data
                }, status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error creating product: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return Response(
                {'error': f'Error creating product: {str(e)}', 'traceback': error_traceback if settings.DEBUG else None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminProductUpdateAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
            # Create a mutable copy of request.data (QueryDict)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
            # If img_url is not in request.FILES (no new image uploaded), remove it from data to preserve existing image
            if 'img_url' not in request.FILES:
                data.pop('img_url', None)
            
            serializer = ProductSerializer(product, data=data, partial=True)
            if serializer.is_valid():
                updated_product = serializer.save()
                return Response({
                    'message': 'Product updated successfully',
                    'product': ProductSerializer(updated_product).data
                }, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error updating product: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return Response(
                {'error': f'Error updating product: {str(e)}', 'traceback': error_traceback if settings.DEBUG else None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
            # Create a mutable copy of request.data (QueryDict)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
            # If img_url is not in request.FILES (no new image uploaded), remove it from data
            # Django will automatically preserve the existing image when the field is not provided
            if 'img_url' not in request.FILES:
                data.pop('img_url', None)
            
            serializer = ProductSerializer(product, data=data)
            if serializer.is_valid():
                updated_product = serializer.save()
                return Response({
                    'message': 'Product updated successfully',
                    'product': ProductSerializer(updated_product).data
                }, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Validation failed', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error updating product: {str(e)}")
            print(f"Traceback: {error_traceback}")
            return Response(
                {'error': f'Error updating product: {str(e)}', 'traceback': error_traceback if settings.DEBUG else None},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['DELETE'])
@permission_classes([IsAdminOrSuperAdmin])
def delete_product(request, product_id):
    """Delete product"""
    try:
        product = Product.objects.get(id=product_id)
        product.delete()
        return Response(
            {'message': 'Product deleted successfully'},
            status=status.HTTP_200_OK
        )
    except Product.DoesNotExist:
        return Response(
            {'error': 'Product not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error deleting product: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def admin_orders_list(request):
    """Get orders list for admin panel"""
    try:
        from home.models import Order, OrderItem
        
        search = request.query_params.get('search', '')
        status_filter = request.query_params.get('status', 'all')
        payment_status_filter = request.query_params.get('payment_status', 'all')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        orders = Order.objects.all().select_related('user').prefetch_related('items').order_by('-created_at')
        
        if search:
            orders = orders.filter(
                Q(order_number__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(shipping_name__icontains=search)
            )
        
        if status_filter != 'all':
            orders = orders.filter(status=status_filter)
        
        if payment_status_filter != 'all':
            orders = orders.filter(payment_status=payment_status_filter)
        
        # Manual pagination
        total = orders.count()
        start = (page - 1) * page_size
        end = start + page_size
        orders_page = orders[start:end]
        
        orders_data = []
        for order in orders_page:
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'id': str(item.id),
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'price': str(item.product_price),
                    'subtotal': str(item.subtotal),
                    'size': item.size or '',
                    'color': item.color or '',
                })
            
            orders_data.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'user': {
                    'id': str(order.user.id),
                    'username': order.user.username,
                    'email': order.user.email,
                },
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display(),
                'razorpay_payment_id': order.razorpay_payment_id or '',
                'razorpay_order_id': order.razorpay_order_id or '',
                'shipping_name': order.shipping_name,
                'shipping_address': order.shipping_address,
                'shipping_city': order.shipping_city,
                'shipping_state': order.shipping_state,
                'shipping_postal_code': order.shipping_postal_code,
                'shipping_country': order.shipping_country,
                'shipping_phone': order.shipping_phone or '',
                'subtotal': str(order.subtotal),
                'shipping_cost': str(order.shipping_cost),
                'tax': str(order.tax),
                'total': str(order.total),
                'items': items_data,
                'items_count': len(items_data),
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
            })
        
        return Response({
            'orders': orders_data,
            'count': total,
            'page': page,
            'page_size': page_size,
            'num_pages': (total + page_size - 1) // page_size
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error loading orders: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def get_order(request, order_id):
    """Get single order by ID"""
    try:
        from home.models import Order
        
        order = Order.objects.select_related('user').prefetch_related('items').get(id=order_id)
        
        items_data = []
        for item in order.items.all():
            items_data.append({
                'id': str(item.id),
                'product_name': item.product_name,
                'quantity': item.quantity,
                'price': str(item.product_price),
                'subtotal': str(item.subtotal),
                'size': item.size or '',
                'color': item.color or '',
            })
        
        return Response({
            'id': str(order.id),
            'order_number': order.order_number,
            'user': {
                'id': str(order.user.id),
                'username': order.user.username,
                'email': order.user.email,
            },
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_status': order.payment_status,
            'payment_status_display': order.get_payment_status_display(),
            'razorpay_payment_id': order.razorpay_payment_id or '',
            'razorpay_order_id': order.razorpay_order_id or '',
            'shipping_name': order.shipping_name,
            'shipping_address': order.shipping_address,
            'shipping_city': order.shipping_city,
            'shipping_state': order.shipping_state,
            'shipping_postal_code': order.shipping_postal_code,
            'shipping_country': order.shipping_country,
            'shipping_phone': order.shipping_phone or '',
            'subtotal': str(order.subtotal),
            'shipping_cost': str(order.shipping_cost),
            'tax': str(order.tax),
            'total': str(order.total),
            'items': items_data,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'updated_at': order.updated_at.isoformat() if order.updated_at else None,
        }, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error loading order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAdminOrSuperAdmin])
def update_order_status(request, order_id):
    """Update order status and auto-process refunds if status is 'processing'"""
    try:
        from home.models import Order, ReturnRequest
        from django.utils import timezone
        from django.conf import settings
        import razorpay
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        
        order = Order.objects.get(id=order_id)
        data = request.data
        old_status = order.status
        
        # Update status if provided
        if 'status' in data:
            status_value = data['status']
            valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
            if status_value not in valid_statuses:
                return Response(
                    {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.status = status_value
        
        # Update payment_status if provided
        if 'payment_status' in data:
            payment_status_value = data['payment_status']
            valid_payment_statuses = [choice[0] for choice in Order.PAYMENT_STATUS_CHOICES]
            if payment_status_value not in valid_payment_statuses:
                return Response(
                    {'error': f'Invalid payment status. Must be one of: {", ".join(valid_payment_statuses)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            order.payment_status = payment_status_value
        
        order.save()
        
        # If order status is changed to 'processing', automatically process refunds for pending return requests
        if 'status' in data and status_value == 'processing' :
            logger.info(f"Order status changed to 'processing' for Order: {order.order_number} (ID: {order.id})")
            print(f"[ORDER REFUND] Order status changed to 'processing' for Order: {order.order_number} (ID: {order.id})")
            
            # Get all pending return requests for this order
            return_requests = ReturnRequest.objects.filter(
                order=order,
                status='pending'
            ).select_related('order_item')
            
            if return_requests.exists():
                logger.info(f"Found {return_requests.count()} pending return request(s) for order {order.order_number}")
                print(f"[ORDER REFUND] Found {return_requests.count()} pending return request(s) for order {order.order_number}")
                
                # Check if order has payment
                if order.razorpay_payment_id:
                    logger.info(f"Order has Razorpay Payment ID: {order.razorpay_payment_id}. Processing refunds...")
                    print(f"[ORDER REFUND] Order has Razorpay Payment ID: {order.razorpay_payment_id}. Processing refunds...")
                    
                    # Initialize Razorpay client
                    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    
                    # Process refund for each return request
                    for return_request in return_requests:
                        if return_request.razorpay_refund_id:
                            logger.warning(f"Return Request {return_request.id} already has refund ID: {return_request.razorpay_refund_id}. Skipping...")
                            print(f"[ORDER REFUND] Return Request {return_request.id} already has refund ID: {return_request.razorpay_refund_id}. Skipping...")
                            continue
                        
                        try:
                            # Calculate refund amount (proportional to quantity returned)
                            item_total = float(return_request.order_item.subtotal)
                            item_quantity = return_request.order_item.quantity
                            return_quantity = return_request.quantity
                            refund_amount = (item_total / item_quantity) * return_quantity
                            
                            # Convert to paise (Razorpay uses smallest currency unit)
                            refund_amount_paise = int(refund_amount * 100)
                            
                            logger.info(f"Processing refund for Return Request {return_request.id} - Amount: Rs. {refund_amount} ({refund_amount_paise} paise)")
                            print(f"[ORDER REFUND] Processing refund for Return Request {return_request.id} - Amount: Rs. {refund_amount} ({refund_amount_paise} paise)")
                            
                        # Create refund via Razorpay
                            refund_data = {
                            'amount': refund_amount_paise,
                            'speed': 'normal',  # or 'optimum' for faster refunds
                            'notes': {
                                'return_request_id': str(return_request.id),
                                'order_number': order.razorpay_order_id,
                                # 'razorpay_order_id': order.razorpay_order_id or '',
                                'reason': return_request.get_reason_display(),
                            }
                        }
                            
                            logger.info(f"Calling Razorpay refund API - Payment ID: {order.razorpay_payment_id}, Amount: {refund_amount_paise} paise")
                            print(f"[ORDER REFUND] Calling Razorpay refund API - Payment ID: {order.razorpay_payment_id}, Amount: {refund_amount_paise} paise")
                            print(f"[ORDER REFUND] Refund Data: {refund_data}")
                            
                            refund_response = razorpay_client.payment.refund(
                                order.razorpay_payment_id,
                                refund_data
                            )
                            
                            logger.info(f"Razorpay refund API response received: {refund_response}")
                            print(f"[ORDER REFUND] Razorpay refund API response received: {refund_response}")
                            print(f"[ORDER REFUND] Got the refund from Razorpay - Refund ID: {refund_response.get('id')}, Amount: Rs. {refund_amount}, Order: {order.order_number}, Return Request: {return_request.id}")
                            logger.info(f"Got the refund from Razorpay - Refund ID: {refund_response.get('id')}, Amount: Rs. {refund_amount}, Order: {order.order_number}, Return Request: {return_request.id}")
                            
                            # Update return request with refund details
                            return_request.refund_amount = Decimal(str(refund_amount))
                            return_request.razorpay_refund_id = refund_response.get('id')
                            return_request.refund_status = refund_response.get('status', 'processed')
                            return_request.status = 'completed'
                            return_request.refunded_at = timezone.now()
                            return_request.processed_by = request.user
                            return_request.processed_at = timezone.now()
                            return_request.save()
                            
                            logger.info(f"Return request {return_request.id} updated with refund details. Status changed to 'completed'")
                            print(f"[ORDER REFUND] Return request {return_request.id} updated with refund details. Status changed to 'completed'")
                            
                            # Send email notifications
                            logger.info(f"Sending refund notification emails for Return Request {return_request.id}")
                            print(f"[ORDER REFUND] Sending refund notification emails for Return Request {return_request.id}")
                            send_refund_notification_emails(return_request, refund_response, refund_amount)
                            
                        except razorpay.errors.BadRequestError as e:
                            logger.error(f"Razorpay refund API error for Return Request {return_request.id} (BadRequestError): {str(e)}")
                            print(f"[ORDER REFUND ERROR] Razorpay refund API error for Return Request {return_request.id} (BadRequestError): {str(e)}")
                            # Continue with other return requests even if one fails
                            continue
                        except Exception as e:
                            logger.error(f"Error processing refund for Return Request {return_request.id}: {str(e)}", exc_info=True)
                            print(f"[ORDER REFUND ERROR] Error processing refund for Return Request {return_request.id}: {str(e)}")
                            import traceback
                            print(f"[ORDER REFUND ERROR] Traceback: {traceback.format_exc()}")
                            # Continue with other return requests even if one fails
                            continue
                    
                    # Update order payment status and order status if all items are refunded
                    total_refunded = sum(float(req.refund_amount) for req in return_requests if req.refund_amount)
                    if total_refunded >= float(order.total):
                        order.payment_status = 'refunded'
                        order.status = 'refunded'
                        order.save()
                        logger.info(f"Order payment status and order status updated to 'refunded' (full refund)")
                        print(f"[ORDER REFUND] Order payment status and order status updated to 'refunded' (full refund)")
                else:
                    logger.warning(f"Order {order.order_number} does not have Razorpay Payment ID. Cannot process refunds.")
                    print(f"[ORDER REFUND] Order {order.order_number} does not have Razorpay Payment ID. Cannot process refunds.")
            else:
                logger.info(f"No pending return requests found for order {order.order_number}")
                print(f"[ORDER REFUND] No pending return requests found for order {order.order_number}")
        
        return Response({
            'message': 'Order updated successfully',
            'order': {
                'id': str(order.id),
                'order_number': order.order_number,
                'status': order.status,
                'status_display': order.get_status_display(),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display(),
            }
        }, status=status.HTTP_200_OK)
    
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error updating order: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def admin_return_requests_list(request):
    """Get return requests list for admin panel"""
    try:
        from home.models import ReturnRequest
        
        status_filter = request.query_params.get('status', 'all')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        return_requests = ReturnRequest.objects.all().select_related(
            'order', 'order_item', 'user', 'processed_by'
        ).order_by('-created_at')
        
        if status_filter != 'all':
            return_requests = return_requests.filter(status=status_filter)
        
        # Manual pagination
        total = return_requests.count()
        start = (page - 1) * page_size
        end = start + page_size
        requests_page = return_requests[start:end]
        
        requests_data = []
        for req in requests_page:
            requests_data.append({
                'id': str(req.id),
                'order_number': req.order.order_number,
                'order_id': str(req.order.id),
                'product_name': req.order_item.product_name,
                'quantity': req.quantity,
                'reason': req.get_reason_display(),
                'reason_description': req.reason_description or '',
                'status': req.status,
                'status_display': req.get_status_display(),
                'admin_notes': req.admin_notes or '',
                'user': {
                    'id': str(req.user.id),
                    'username': req.user.username,
                    'email': req.user.email,
                },
                'processed_by': {
                    'id': str(req.processed_by.id),
                    'username': req.processed_by.username,
                } if req.processed_by else None,
                'refund_amount': str(req.refund_amount) if req.refund_amount else None,
                'razorpay_refund_id': req.razorpay_refund_id or '',
                'refund_status': req.refund_status or '',
                'created_at': req.created_at.isoformat() if req.created_at else None,
                'updated_at': req.updated_at.isoformat() if req.updated_at else None,
                'processed_at': req.processed_at.isoformat() if req.processed_at else None,
                'refunded_at': req.refunded_at.isoformat() if req.refunded_at else None,
            })
        
        return Response({
            'return_requests': requests_data,
            'count': total,
            'page': page,
            'page_size': page_size,
            'num_pages': (total + page_size - 1) // page_size
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Error loading return requests: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH', 'PUT'])
@permission_classes([IsAdminOrSuperAdmin])
def update_return_request_status(request, return_request_id):
    """Update return request status and auto-process refund if status is 'processing'"""
    try:
        from home.models import ReturnRequest, Order
        from django.utils import timezone
        from django.conf import settings
        import razorpay
        from decimal import Decimal
        
        return_request = ReturnRequest.objects.select_related('order', 'order_item').get(id=return_request_id)
        data = request.data
        
        old_status = return_request.status
        
        # Update status if provided
        if 'status' in data:
            status_value = data['status']
            valid_statuses = [choice[0] for choice in ReturnRequest.STATUS_CHOICES]
            if status_value not in valid_statuses:
                return Response(
                    {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return_request.status = status_value
            
            # Set processed_by and processed_at if status is being changed from pending
            if return_request.status != 'pending' and not return_request.processed_by:
                return_request.processed_by = request.user
                return_request.processed_at = timezone.now()
        
        # Update admin notes if provided
        if 'admin_notes' in data:
            return_request.admin_notes = data['admin_notes']
        
        # If status is changed to 'processing', automatically process refund
        if 'status' in data and status_value == 'processing' and old_status != 'processing':
            import logging
            logger = logging.getLogger(__name__)
            
            order = return_request.order
            
            logger.info(f"Status changed to 'processing' for Return Request: {return_request.id}, Order: {order.order_number}")
            print(f"[RETURN REFUND] Status changed to 'processing' for Return Request: {return_request.id}, Order: {order.order_number}")
            
            # Check if order has payment
            if order.razorpay_payment_id:
                logger.info(f"Order has Razorpay Payment ID: {order.razorpay_payment_id}. Proceeding with refund...")
                print(f"[RETURN REFUND] Order has Razorpay Payment ID: {order.razorpay_payment_id}. Proceeding with refund...")
                
                # Check if refund already processed
                if not return_request.razorpay_refund_id:
                    try:
                        # Calculate refund amount (proportional to quantity returned)
                        item_total = float(return_request.order_item.subtotal)
                        item_quantity = return_request.order_item.quantity
                        return_quantity = return_request.quantity
                        refund_amount = (item_total / item_quantity) * return_quantity
                        
                        # Convert to paise (Razorpay uses smallest currency unit)
                        refund_amount_paise = int(refund_amount * 100)
                        
                        logger.info(f"Calculated refund amount: Rs. {refund_amount} ({refund_amount_paise} paise)")
                        print(f"[RETURN REFUND] Calculated refund amount: Rs. {refund_amount} ({refund_amount_paise} paise)")
                        
                        # Initialize Razorpay client
                        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                        
                        # Create refund via Razorpay
                        refund_data = {
                            'amount': refund_amount_paise,
                            'speed': 'normal',  # or 'optimum' for faster refunds
                            'notes': {
                                'return_request_id': str(return_request.id),
                                'order_number': order.order_number,
                                'razorpay_order_id': order.razorpay_order_id or '',
                                'reason': return_request.get_reason_display(),
                            }
                        }
                        
                        logger.info(f"Calling Razorpay refund API - Payment ID: {order.razorpay_payment_id}, Amount: {refund_amount_paise} paise")
                        print(f"[RETURN REFUND] Calling Razorpay refund API - Payment ID: {order.razorpay_payment_id}, Amount: {refund_amount_paise} paise")
                        print(f"[RETURN REFUND] Refund Data: {refund_data}")
                        
                        refund_response = razorpay_client.payment.refund(
                            order.razorpay_payment_id,
                            refund_data
                        )
                        
                        logger.info(f"Razorpay refund API response received: {refund_response}")
                        print(f"[RETURN REFUND] Razorpay refund API response received: {refund_response}")
                        print(f"[RETURN REFUND] Got the refund from Razorpay - Refund ID: {refund_response.get('id')}, Amount: Rs. {refund_amount}, Order: {order.order_number}, Return Request: {return_request.id}")
                        logger.info(f"Got the refund from Razorpay - Refund ID: {refund_response.get('id')}, Amount: Rs. {refund_amount}, Order: {order.order_number}, Return Request: {return_request.id}")
                        
                        # Update return request with refund details
                        return_request.refund_amount = Decimal(str(refund_amount))
                        return_request.razorpay_refund_id = refund_response.get('id')
                        return_request.refund_status = refund_response.get('status', 'processed')
                        return_request.status = 'completed'  # Auto-complete after refund
                        return_request.refunded_at = timezone.now()
                        
                        logger.info(f"Return request updated with refund details. Status changed to 'completed'")
                        print(f"[RETURN REFUND] Return request updated with refund details. Status changed to 'completed'")
                        
                        # Update order payment status and order status if full refund
                        if refund_amount >= float(order.total):
                            order.payment_status = 'refunded'
                            order.status = 'refunded'
                            order.save()
                            logger.info(f"Order payment status and order status updated to 'refunded' (full refund)")
                            print(f"[RETURN REFUND] Order payment status and order status updated to 'refunded' (full refund)")
                        
                        # Send email notifications
                        logger.info(f"Sending refund notification emails to admin and user")
                        print(f"[RETURN REFUND] Sending refund notification emails to admin and user")
                        send_refund_notification_emails(return_request, refund_response, refund_amount)
                        
                    except razorpay.errors.BadRequestError as e:
                        logger.error(f"Razorpay refund API error (BadRequestError): {str(e)}")
                        print(f"[RETURN REFUND ERROR] Razorpay refund API error (BadRequestError): {str(e)}")
                        return Response(
                            {'error': f'Razorpay refund error: {str(e)}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    except Exception as e:
                        # Log error but continue with status update
                        logger.error(f"Error processing refund automatically: {str(e)}", exc_info=True)
                        print(f"[RETURN REFUND ERROR] Error processing refund automatically: {str(e)}")
                        import traceback
                        print(f"[RETURN REFUND ERROR] Traceback: {traceback.format_exc()}")
                        # Don't fail the status update, just log the error
                else:
                    logger.warning(f"Refund already processed for Return Request: {return_request.id}. Razorpay Refund ID: {return_request.razorpay_refund_id}")
                    print(f"[RETURN REFUND] Refund already processed for Return Request: {return_request.id}. Razorpay Refund ID: {return_request.razorpay_refund_id}")
            else:
                logger.warning(f"Order does not have Razorpay Payment ID. Cannot process refund. Order: {order.order_number}")
                print(f"[RETURN REFUND] Order does not have Razorpay Payment ID. Cannot process refund. Order: {order.order_number}")
        
        return_request.save()
        
        return Response({
            'message': 'Return request updated successfully',
            'return_request': {
                'id': str(return_request.id),
                'status': return_request.status,
                'status_display': return_request.get_status_display(),
                'admin_notes': return_request.admin_notes or '',
                'refund_amount': str(return_request.refund_amount) if return_request.refund_amount else None,
                'razorpay_refund_id': return_request.razorpay_refund_id or '',
                'refund_status': return_request.refund_status or '',
            }
        }, status=status.HTTP_200_OK)
    
    except ReturnRequest.DoesNotExist:
        return Response(
            {'error': 'Return request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error updating return request: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def process_refund(request, return_request_id):
    """Process refund via Razorpay for a return request"""
    try:
        from home.models import ReturnRequest, Order
        from django.utils import timezone
        from django.conf import settings
        import razorpay
        from decimal import Decimal
        
        return_request = ReturnRequest.objects.select_related('order', 'order_item').get(id=return_request_id)
        data = request.data
        
        # Validate return request status - should be processing or approved
        if return_request.status not in ['processing', 'approved']:
            return Response(
                {'error': 'Refund can only be processed for return requests with status "processing" or "approved"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if order has payment
        order = return_request.order
        if not order.razorpay_payment_id:
            return Response(
                {'error': 'Order does not have a Razorpay payment ID. Cannot process refund.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate refund amount (proportional to quantity returned)
        refund_amount = data.get('refund_amount')
        if not refund_amount:
            # Calculate proportional refund based on quantity
            item_total = float(return_request.order_item.subtotal)
            item_quantity = return_request.order_item.quantity
            return_quantity = return_request.quantity
            refund_amount = (item_total / item_quantity) * return_quantity
        else:
            refund_amount = float(refund_amount)
        
        # Convert to paise (Razorpay uses smallest currency unit)
        refund_amount_paise = int(refund_amount * 100)
        
        # Initialize Razorpay client
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Create refund via Razorpay
        try:
            refund_data = {
                'amount': refund_amount_paise,
                'speed': 'normal',  # or 'optimum' for faster refunds
                'notes': {
                    'return_request_id': str(return_request.id),
                    'order_number': order.order_number,
                    'razorpay_order_id': order.razorpay_order_id or '',
                    'reason': return_request.get_reason_display(),
                }
            }
            
            refund_response = razorpay_client.payment.refund(
                order.razorpay_payment_id,
                refund_data
            )
            
            # Log successful refund
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Got the refund from Razorpay - Refund ID: {refund_response.get('id')}, Amount: Rs. {refund_amount}, Order: {order.order_number}, Return Request: {return_request.id}")
            print(f"Got the refund from Razorpay - Refund ID: {refund_response.get('id')}, Amount: Rs. {refund_amount}, Order: {order.order_number}, Return Request: {return_request.id}")
            
            # Update return request with refund details
            return_request.refund_amount = Decimal(str(refund_amount))
            return_request.razorpay_refund_id = refund_response.get('id')
            return_request.refund_status = refund_response.get('status', 'processed')
            return_request.status = 'completed'
            return_request.refunded_at = timezone.now()
            
            if not return_request.processed_by:
                return_request.processed_by = request.user
                return_request.processed_at = timezone.now()
            
            return_request.save()
            
            # Update order payment status and order status if full refund
            if refund_amount >= float(order.total):
                order.payment_status = 'refunded'
                order.status = 'refunded'
                order.save()
            
            # Send email notifications
            send_refund_notification_emails(return_request, refund_response, refund_amount)
            
            return Response({
                'message': 'Refund processed successfully',
                'refund': {
                    'id': refund_response.get('id'),
                    'amount': refund_amount,
                    'status': refund_response.get('status'),
                    'created_at': refund_response.get('created_at'),
                },
                'return_request': {
                    'id': str(return_request.id),
                    'status': return_request.status,
                    'status_display': return_request.get_status_display(),
                    'refund_amount': str(return_request.refund_amount),
                    'refund_status': return_request.refund_status,
                }
            }, status=status.HTTP_200_OK)
            
        except razorpay.errors.BadRequestError as e:
            return Response(
                {'error': f'Razorpay refund error: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error processing refund: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    except ReturnRequest.DoesNotExist:
        return Response(
            {'error': 'Return request not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error processing refund: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def send_refund_notification_emails(return_request, refund_response, refund_amount):
    """Send email notifications to admin and user after refund is processed"""
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        order = return_request.order
        user = return_request.user
        
        # Get admin email
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'admin@vhinternaltional.com')
        
        # Prepare email context
        context = {
            'return_request': return_request,
            'order': order,
            'order_item': return_request.order_item,
            'user': user,
            'refund_amount': refund_amount,
            'refund_id': refund_response.get('id'),
            'refund_status': refund_response.get('status'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Send email to admin
        admin_subject = f'Refund Processed - Order {order.order_number}'
        admin_message = render_to_string('home/emails/refund_notification_admin.html', context)
        
        send_mail(
            subject=admin_subject,
            message='',  # Plain text version (optional)
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@vhinternaltional.com'),
            recipient_list=[admin_email],
            html_message=admin_message,
            fail_silently=False,
        )
        
        # Send email to user
        user_subject = f'Refund Processed for Order {order.order_number}'
        user_message = render_to_string('home/emails/refund_notification_user.html', context)
        
        send_mail(
            subject=user_subject,
            message='',  # Plain text version (optional)
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@vhinternaltional.com'),
            recipient_list=[user.email],
            html_message=user_message,
            fail_silently=False,
        )
        
    except Exception as e:
        # Log error but don't fail the refund process
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending refund notification emails: {str(e)}")
        print(f"Error sending refund notification emails: {str(e)}")

