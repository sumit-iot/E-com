from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from products.serializers import ProductListSerializer
from products.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer with product details"""
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'size', 'color', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """Cart serializer with items"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CartItemCreateSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    size = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    color = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'size', 'color', 'subtotal']
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    """Order serializer with items"""
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'user', 'order_number', 'status', 'payment_status',
            'shipping_name', 'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country', 'shipping_phone',
            'subtotal', 'shipping_cost', 'tax', 'total',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'order_number', 'created_at', 'updated_at']


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    shipping_name = serializers.CharField(max_length=255)
    shipping_address = serializers.CharField()
    shipping_city = serializers.CharField(max_length=100)
    shipping_state = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20)
    shipping_country = serializers.CharField(max_length=100, default='India')
    shipping_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)


