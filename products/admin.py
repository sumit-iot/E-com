from django.contrib import admin
from .models import ProductCategory, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'discount', 'is_active', 'created_on', 'modified_on')
    list_filter = ('is_active', 'created_on')
    search_fields = ('category_name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_category', 'cost', 'quantity', 'discount', 'is_active', 'no_of_purchase', 'created_on')
    list_filter = ('is_active', 'product_category', 'created_on')
    search_fields = ('name', 'description')
    raw_id_fields = ('product_category',)
