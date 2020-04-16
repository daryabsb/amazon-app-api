from rest_framework import serializers
from core.models import Tag, Category, Product


class TagSerializer(serializers.ModelSerializer):
    # Serializer for tag objects
    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_Fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    # Serializer for category objects
    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    # Serialize a product

    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Product
        fields = ('id', 'title', 'categories', 'tags', 'time_minutes',
                  'price', 'link'
                  )
        read_only_Fields = ('id',)


class ProductDetailSerializer(ProductSerializer):
    # Serializer a product detail
    categories = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)


class ProductImageSerializer(serializers.ModelSerializer):
    # Serializer for uploading images for products

    class Meta:
        model = Product
        fields = ('id', 'image')
        read_only_Fields = ('id',)
