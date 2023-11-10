"""
tests for the ingredients API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_ingredient_url(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='testpass123'):
    """
    Create and return User object
    """
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsAPITests(TestCase):
    """
    Test public API requests.
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test unauthenticated request.
        """
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """
    Test authenticated API requests.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_ingredients(self):
        """
        Test retrieving a list of ingredients.
        """
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Vanilla")

        res = self.client.get(INGREDIENTS_URL)

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Test compare serializer data with response data
        ingredients = Ingredient.objects.filter(user=self.user).order_by('-name')
        self.assertEqual(len(ingredients), 2)

        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """
        Test list of ingredients is limited to authenticated user.
        """
        user2 = create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='Salt')
        ingredient = Ingredient.objects.create(user=self.user, name='Pepper')

        res = self.client.get(INGREDIENTS_URL)

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Test data
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """
        Test update ingredient name
        """
        ingredient = Ingredient.objects.create(user=self.user, name="Test name")

        # Make a patch request to update name of the ingredient.
        res = self.client.patch(detail_ingredient_url(ingredient.id), {
            'name': 'updated name'
        })

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Test name change
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, 'updated name')

    def test_other_user_ingredient_update(self):
        """
        Test other user ingredient update.
        """
        user2 = create_user(email='user2@example.com')
        ingredient_user2 = Ingredient.objects.create(user=user2, name="User 2 Ingredient")

        payload = {'name': 'Updated name'}

        # Try to update user2 ingredient
        url = detail_ingredient_url(ingredient_user2.id)
        self.client.patch(url, payload)

        ingredient_user2.refresh_from_db()
        self.assertEqual(ingredient_user2.name, 'User 2 Ingredient')
