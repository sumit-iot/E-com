from rest_framework.routers import DefaultRouter
from .views import ProductCategoryViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = router.urls


