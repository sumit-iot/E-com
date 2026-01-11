from django.db import models
import uuid
from django.utils import timezone


class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=50, blank=False, null=False)
    img_url = models.ImageField(upload_to='category_images/', null=True, blank=True)
    discount = models.IntegerField(default=0, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100, blank=False)
    created_on = models.DateTimeField(default=timezone.now)
    modified_by = models.CharField(max_length=100, blank=False)
    modified_on = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'product_category'
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.category_name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    name = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(null=True, blank=True)
    cost = models.IntegerField(null=False, blank=False, default=0)
    quantity = models.IntegerField(null=False, blank=False, default=0)
    img_url = models.ImageField(upload_to='product_images/', null=True, blank=True)
    discount = models.IntegerField(default=0, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100, blank=False)
    created_on = models.DateTimeField(default=timezone.now)
    modified_by = models.CharField(max_length=100, blank=False)
    modified_on = models.DateTimeField(default=timezone.now)
    product_category = models.ForeignKey(ProductCategory, null=True, blank=True, on_delete=models.DO_NOTHING)
    no_of_purchase = models.IntegerField(default=0)

    class Meta:
        db_table = 'product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        if self.discount and self.discount > 0:
            return self.cost - (self.cost * self.discount / 100)
        return self.cost
