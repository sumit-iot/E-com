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
        
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        total_orders = 0
        pending_orders = 0
        total_users = User.objects.count()
        total_customers = User.objects.filter(user_type='common').count()
        revenue = 0
        
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
            return Response(
                {'error': f'Error creating category: {str(e)}'},
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
            return Response(
                {'error': f'Error updating category: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, category_id, *args, **kwargs):
        try:
            category = ProductCategory.objects.get(id=category_id)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
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
            return Response(
                {'error': f'Error updating category: {str(e)}'},
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
            return Response(
                {'error': f'Error creating product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminProductUpdateAPIView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
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
            return Response(
                {'error': f'Error updating product: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, product_id, *args, **kwargs):
        try:
            product = Product.objects.get(id=product_id)
            data = request.data.copy()
            data['modified_by'] = request.user.username
            
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
            return Response(
                {'error': f'Error updating product: {str(e)}'},
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

