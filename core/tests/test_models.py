"""
Test models
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from core import models


def create_user(email='user@example.com', password='testpass123'):
    """
    Create and return a new user instance.
    """
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """
        Test the email for a new user is normalized.
        """
        samples = [
            ["test1@example.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"]
        ]

        for email, expected in samples:
            with self.subTest(email=email):
                user = get_user_model().objects.create_user(
                    email=email,
                    password="testpass123"
                )
                self.assertEqual(user.email, expected)

    def test_new_user_without_email(self):
        """
        Test creating user without email raises error.
        """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password="testpass123"
            )

    def test_create_new_superuser(self):
        """
        Test creating a new superuser.
        """
        user = get_user_model().objects.create_superuser(
            email="test1@example.com",
            password="testpass123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test create a recipe is successful"""
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )

        recipe = models.Recipe(
            user=user,
            title="Sample recipe name",
            time_minutes=5,
            price=Decimal('5.50'),
            description="Sample recipe description"
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """
        Test creating tag successful.
        """
        user = create_user()
        tag = models.Tag.objects.create(user=user, name='Tag1')

        self.assertEqual(str(tag), tag.name)
        self.assertEqual(tag.user, user)

    def test_ingredient_create(self):
        """
        Test creating an ingredient is successful.
        """
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            name="Test Ingredient",
            user=user
        )

        self.assertEqual(str(ingredient), ingredient.name)
        self.assertEqual(ingredient.name, 'Test Ingredient')
        self.assertEqual(ingredient.user, user)
