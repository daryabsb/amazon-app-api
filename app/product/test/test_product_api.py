import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Product, Tag, Category
from product.serializers import ProductSerializer, ProductDetailSerializer

PRODUCTS_URL = reverse('product:myproduct-list')


def image_upload_url(product_id):
    # Return url for product image upload
    return reverse('product:product-upload-image', args=[product_id])


def detail_url(product_id):
    # Getting product detail url
    return reverse('product:product-detail', args=[product_id])


def sample_tag(user, name='Main Course'):
    # Create and return a sample tag
    return Tag.objects.create(user=user, name=name)


def sample_category(user, name='Main Course'):
    # Create and return a sample category
    return Category.objects.create(user=user, name=name)


def sample_product(user, **params):
    # Create a sample product
    defaults = {
        'title': 'Sample Product',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Product.objects.create(user=user, **defaults)


class PublicProductAPITest(TestCase):
    # Test unauthenticated product api test

    def setUp(self):
        self.client = APIClient()

    def test_required_auth(self):
        # Test that authentication is required
        res = self.client.get(PRODUCTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateProductAPITest(TestCase):
    # Test unauthenticated product API cases

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'root@root.com',
            'Welcome1234'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_products(self):
        # Test retrieving a list of products
        sample_product(user=self.user)
        sample_product(user=self.user)

        res = self.client.get(PRODUCTS_URL)

        products = Product.objects.all().order_by('-id')
        serializer = ProductSerializer(products, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_products_limited_to_user(self):
        # Test that products in the list belong to the auth user
        user2 = get_user_model().objects.create_user(
            'zane@darya.com',
            'Welcome2431'
        )
        sample_product(user=user2)
        sample_product(user=self.user)

        res = self.client.get(PRODUCTS_URL)

        products = Product.objects.filter(user=self.user)
        serializer = ProductSerializer(products, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_product_detail(self):
        # Test viewing product detail
        product = sample_product(user=self.user)
        product.tags.add(sample_tag(user=self.user))
        product.categories.add(sample_category(user=self.user))

        url = detail_url(product.id)
        res = self.client.get(url)

        serializer = ProductDetailSerializer(product)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_product(self):
        # Test creating product
        payload = {
            'title': 'Chocolate Cheescake',
            'time_minutes': 30,
            'price': 5.00
        }
        res = self.client.post(PRODUCTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(product, key))

    def test_create_product_with_tags(self):
        """Test creating a product with tags"""
        tag1 = sample_tag(user=self.user, name='Tag 1')
        tag2 = sample_tag(user=self.user, name='Tag 2')
        payload = {
            'title': 'Test product with two tags',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 30,
            'price': 10.00
        }
        res = self.client.post(PRODUCTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(id=res.data['id'])
        tags = product.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_product_with_categories(self):
        """Test creating product with categories"""
        category1 = sample_category(user=self.user, name='Category 1')
        category2 = sample_category(user=self.user, name='Category 2')
        payload = {
            'title': 'Test product with categories',
            'categories': [category1.id, category2.id],
            'time_minutes': 45,
            'price': 15.00
        }

        res = self.client.post(PRODUCTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(id=res.data['id'])
        categories = product.categories.all()
        self.assertEqual(categories.count(), 2)
        self.assertIn(category1, categories)
        self.assertIn(category2, categories)

    def test_partial_update_product(self):
        # Test updating product with patch

        product = sample_product(user=self.user)
        product.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Curry')

        payload = {'title': 'Chicken Tika', 'tags': [new_tag.id]}

        url = detail_url(product.id)
        self.client.patch(url, payload)

        product.refresh_from_db()
        self.assertEqual(product.title, payload['title'])

        tags = product.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_product(self):
        # Test updating a product with put

        product = sample_product(user=self.user)
        product.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Spagheti Carbonaro',
            'time_minutes': 25,
            'price': 5.00
        }

        url = detail_url(product.id)
        self.client.put(url, payload)
        product.refresh_from_db()

        self.assertEqual(product.title, payload['title'])
        self.assertEqual(product.time_minutes, payload['time_minutes'])
        self.assertEqual(product.price, payload['price'])

        tags = product.tags.all()
        self.assertEqual(len(tags), 0)


class ProductImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'root@root.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)
        self.product = sample_product(user=self.user)

    def tearDown(self):
        self.product.image.delete()

    def test_upload_image_to_product(self):
        # Test uploading an image to the product

        url = image_upload_url(self.product.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.product.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.product.image.path))

    def test_upload_image_bad_request(self):
        # Test uploading invalid image
        url = image_upload_url(self.product.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_products_by_tags(self):
        """Test returning products with specific tags"""
        product1 = sample_product(user=self.user, title='Thai vegetable curry')
        product2 = sample_product(
            user=self.user, title='Aubergine with tahini')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')
        product1.tags.add(tag1)
        product2.tags.add(tag2)
        product3 = sample_product(user=self.user, title='Fish and chips')

        res = self.client.get(
            PRODUCTS_URL,
            {'tags': '{},{}'.format(tag1.id, tag2.id)}
        )

        serializer1 = ProductSerializer(product1)
        serializer2 = ProductSerializer(product2)
        serializer3 = ProductSerializer(product3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_products_by_categories(self):
        """Test returning products with specific categories"""
        product1 = sample_product(user=self.user, title='Posh beans on toast')
        product2 = sample_product(user=self.user, title='Chicken cacciatore')
        category1 = sample_category(user=self.user, name='Feta cheese')
        category2 = sample_category(user=self.user, name='Chicken')
        product1.categories.add(category1)
        product2.categories.add(category2)
        product3 = sample_product(user=self.user, title='Steak and mushrooms')

        res = self.client.get(
            PRODUCTS_URL,
            {'categories': '{},{}'.format(category1.id, category2.id)}
        )

        serializer1 = ProductSerializer(product1)
        serializer2 = ProductSerializer(product2)
        serializer3 = ProductSerializer(product3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
