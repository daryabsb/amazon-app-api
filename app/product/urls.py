from django.urls import path, include
from rest_framework.routers import DefaultRouter

from product import views

router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)
router.register('products', views.ProductViewset)

app_name = 'product'

urlpatterns = [
    path('', include(router.urls))
]
