from rest_framework import serializers
from .models import Product, ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'category_name', 'img_url', 'discount', 'is_active', 'created_by', 'created_on', 'modified_by', 'modified_on']
        read_only_fields = ['id', 'created_on', 'modified_on']
    
    def update(self, instance, validated_data):
        # If img_url is not provided in the update, Django will automatically preserve the existing image
        # We don't need to set it explicitly - just skip it
        return super().update(instance, validated_data)


class ProductCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'category_name', 'img_url', 'discount', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    product_category = ProductCategoryListSerializer(read_only=True)
    product_category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    discounted_price = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'description', 'cost', 'quantity', 'img_url', 'discount',
            'is_active', 'created_by', 'created_on', 'modified_by', 'modified_on',
            'product_category', 'product_category_id', 'no_of_purchase', 'discounted_price'
        ]
        read_only_fields = ['id', 'created_on', 'modified_on', 'discounted_price']

    def create(self, validated_data):
        category_id = validated_data.pop('product_category_id', None)
        if category_id:
            try:
                category = ProductCategory.objects.get(id=category_id)
                validated_data['product_category'] = category
            except ProductCategory.DoesNotExist:
                raise serializers.ValidationError({'product_category_id': 'Category not found'})
        return super().create(validated_data)

    def update(self, instance, validated_data):
        category_id = validated_data.pop('product_category_id', None)
        # If img_url is not provided in the update, Django will automatically preserve the existing image
        # We don't need to set it explicitly - just skip it
        if category_id is not None:
            if category_id:
                try:
                    category = ProductCategory.objects.get(id=category_id)
                    validated_data['product_category'] = category
                except ProductCategory.DoesNotExist:
                    raise serializers.ValidationError({'product_category_id': 'Category not found'})
            else:
                validated_data['product_category'] = None
        return super().update(instance, validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    product_category = ProductCategoryListSerializer(read_only=True)
    discounted_price = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'description', 'cost', 'quantity', 'img_url', 'discount',
            'is_active', 'product_category', 'no_of_purchase', 'discounted_price'
        ]


