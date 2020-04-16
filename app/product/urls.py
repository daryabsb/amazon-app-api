from django.urls import path, include
from rest_framework.routers import DefaultRouter

from product import views

router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('categories', views.CategoryViewSet)
router.register('myproducts', views.ProductViewset, basename='myproducts')
router.register('products', views.MyProductViewset, basename='products')

app_name = 'product'

urlpatterns = [
    path('', include(router.urls)),
]
