from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from django.db.models import Q
from .models import Product, ProductCategory
from .serializers import (
    ProductSerializer, ProductListSerializer,
    ProductCategorySerializer, ProductCategoryListSerializer
)
from rest_framework.pagination import PageNumberPagination


class IsAdminOrReadOnly(IsAdminUser):
    """Permission class that allows read-only access to everyone, but write access only to admins"""
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return super().has_permission(request, view)


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all().order_by('category_name')
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category_name']
    ordering_fields = ['category_name', 'created_on', 'modified_on']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductCategoryListSerializer
        return ProductCategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_on')
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'cost', 'created_on', 'modified_on', 'no_of_purchase']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        discount_only = self.request.query_params.get('discount_only')
        in_stock = self.request.query_params.get('in_stock')
        is_active = self.request.query_params.get('is_active')

        if category_id:
            queryset = queryset.filter(product_category__id=category_id)
        if min_price:
            try:
                queryset = queryset.filter(cost__gte=int(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                queryset = queryset.filter(cost__lte=int(max_price))
            except ValueError:
                pass
        if discount_only == 'true':
            queryset = queryset.filter(discount__gt=0)
        if in_stock == 'true':
            queryset = queryset.filter(quantity__gt=0)
        if is_active is not None:
            queryset = queryset.filter(is_active=(is_active.lower() == 'true'))

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def featured(self, request):
        """Get featured products (top 5 by purchase count)"""
        featured_products = self.get_queryset().filter(is_active=True).order_by('-no_of_purchase')[:5]
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def discounted(self, request):
        """Get discounted products (top 5 by discount percentage)"""
        discounted_products = self.get_queryset().filter(is_active=True, discount__gt=0).order_by('-discount')[:5]
        serializer = self.get_serializer(discounted_products, many=True)
        return Response(serializer.data)
