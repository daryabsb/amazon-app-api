from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='root@root.com', password='Welcome1234'):
    # Create a sample user
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        # Test creating a new user with an email is successful
        email = 'root@root.com'
        password = 'Welcome1234'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        # Test the email for a new user is normalized
        email = 'root@ROOT.Com'
        user = get_user_model().objects.create_user(email, 'test123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        # Test creating user with no  email raises error
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_new_superuser(self):
        # Test creating a superuser
        user = get_user_model().objects.create_superuser(
            'root@root.com',
            'root'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_tag_str(self):
        # Test tag string representation
        tag = models.Tag.objects.create(
            user=sample_user(),
            name='Vegan'
        )

        self.assertEqual(str(tag), tag.name)

    # def test_category_str(self):
    #     # Test the category string representation
    #     category = models.Category.objects.create(
    #         user=sample_user(),
    #         name='Cucumber'
    #     )

    #     self.assertEqual(str(category), category.name)

    def test_product_str(self):
        # Test the product string representation
        product = models.Product.objects.create(
            user=sample_user(),
            title='Steak and Mushroom sauce',
            time_minutes=5,
            price=5.00
        )

        self.assertEqual(str(product), product.title)

    @patch('uuid.uuid4')
    def test_resipe_file_name_uuid(self, mock_uuid):
        # Test that image is saved in the correct location
        uuid = 'test_uuid'
        mock_uuid.return_value = uuid
        file_path = models.product_image_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/product/{uuid}.jpg'
        self.assertEqual(file_path, exp_path)
