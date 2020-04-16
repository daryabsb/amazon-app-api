from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework import viewsets, mixins, status

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, DjangoModelPermissionsOrAnonReadOnly

from core.models import Tag, Category, Product
from product.permissions import IsSupplierOrReadOnly
from product import serializers


class BaseProductAttrViewset(viewsets.GenericViewSet,
                             mixins.ListModelMixin,
                             mixins.CreateModelMixin):
    """Base viewset for user owned product attributes"""
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsSupplierOrReadOnly,)

    def get_queryset(self):
        """Return objects for the current authenticated user only"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(product__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()

    def perform_create(self, serializer):
        """Create a new object"""
        serializer.save(user=self.request.user)


class TagViewSet(BaseProductAttrViewset):
    """Manage tags in the database"""
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer


class CategoryViewSet(BaseProductAttrViewset):
    # Manage categories in the database
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer


class MyProductViewset(viewsets.ReadOnlyModelViewSet):
    # Manage products in the database

    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()


class ProductViewset(viewsets.ModelViewSet, ):
    # Manage products in the database

    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def _params_to_ints(self, qs):
        """Convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        # Retrieve the products to the authenticated user
        tags = self.request.query_params.get('tags')
        categories = self.request.query_params.get('categories')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if categories:
            category_ids = self._params_to_ints(categories)
            queryset = queryset.filter(categories__id__in=category_ids)

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        # return apropriate serializer class
        if self.action == 'retrieve':
            return serializers.ProductDetailSerializer
        elif self.action == 'upload_image':
            return serializers.ProductImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new product"""
        if self.request.user:
            serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        # Upload an image to the product
        product = self.get_object()
        serializer = self.get_serializer(
            product,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
