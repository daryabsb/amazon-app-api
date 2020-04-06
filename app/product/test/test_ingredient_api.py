from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Product
from product.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('product:ingredient-list')


class PublicIngredientAPITest(TestCase):
    # Test the publicly available ingredient api

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        # Test that login is required always
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITest(TestCase):
    # Test the private ingredients api

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'root@root.com',
            'Welcome1234'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        # Test retrieving ingredients list
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        # Test that only ingredient for the authenticated user returned
        user2 = get_user_model().objects.create_user(
            'zane@darya.comDarya@2018',
            'Welcome2431'
        )
        Ingredient.objects.create(user=user2, name='Vineger')

        ingredient = Ingredient.objects.create(user=self.user, name='Tumeric')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successfully(self):
        # Test creating a new ingredient
        payload = {'name': 'Test ingredient'}
        self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_invalid(self):
        # Creating a tag with invalid payload
        payload = {'name': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ingredient_assigned_to_products(self):
        # Test filtering ingredients assigned to products
        ingredient1 = Ingredient.objects.create(
            user=self.user, name='Apple'
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user, name='Turkey'
        )
        product = Product.objects.create(
            title='Apple crumble',
            time_minutes=5,
            price=10.00,
            user=self.user
        )
        product.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """ Test filtering ingredients by assigned returns unique """
        ingredient = Ingredient.objects.create(user=self.user, name='Eggs')
        Ingredient.objects.create(user=self.user, name='Cheese')
        product1 = Product.objects.create(
            title='Eggs benedict',
            time_minutes=30,
            price=12.00,
            user=self.user
        )
        product1.ingredients.add(ingredient)
        product2 = Product.objects.create(
            title='Coriander eggs on toast',
            time_minutes=20,
            price=5.00,
            user=self.user
        )
        product2.ingredients.add(ingredient)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
