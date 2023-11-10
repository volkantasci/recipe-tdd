"""Tests for Recipe API."""

from decimal import Decimal

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)

RECIPES_URL = reverse('recipe:recipe-list')


def recipe_detail_url(recipe_id):
    """Create and return a recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return sample recipe"""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'https://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated tests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')

        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_userK(self):
        """
        Testing recipe list to user.
        """
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'testpass123'
        )
        create_recipe(other_user)
        create_recipe(self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail(self):
        """
        Testing recipe detail
        """
        recipe = create_recipe(user=self.user)
        url = recipe_detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_create(self):
        """
        Test recipe create API.
        """
        payload = {
            'title': 'Sample recipe title',
            'time_minutes': 12,
            'price': Decimal('5.25'),
        }

        # Make a POST request
        res = self.client.post(RECIPES_URL, payload)

        # Test request status code 201 CREATED
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Get created recipe instance from DB
        recipe = Recipe.objects.get(id=res.data['id'])

        # Test every key in the recipe
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        # Test the user for same user is making the request
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """
        Test partial update a recipe
        """

        # Create a new recipe for test
        recipe = create_recipe(self.user)

        # Make a request for change the title of recipe
        res = self.client.patch(recipe_detail_url(recipe.id), {
            'title': 'New title'
        })

        # Test the status of request
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Reload recipe from database
        recipe.refresh_from_db()

        # Test recipe title and make sure is changed to new title
        self.assertEqual(recipe.title, 'New title')

        # test recipe link and make sure isn't change
        self.assertEqual(recipe.link, 'https://example.com/recipe.pdf')

    def test_full_update_recipe(self):
        """
        Test full update a recipe
        """
        # Create a new recipe for test
        recipe = create_recipe(self.user)

        # Make a request for change the title of recipe
        payload = {
            'title': 'Updated recipe title',
            'time_minutes': 32,
            'price': Decimal('5.35'),
            'description': 'Sample description',
            'link': 'https://example.com/recipe.pdf'
        }
        res = self.client.put(recipe_detail_url(recipe.id), payload)

        # Test the status of request
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Reload recipe from database
        recipe.refresh_from_db()

        # Test every key in the recipe
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        # Test the user for same user is making the request
        self.assertEqual(recipe.user, self.user)

    def test_recipe_delete(self):
        """
        Test a delete request to successful deletion.
        """

        # Create a new recipe for test
        recipe = create_recipe(self.user)

        # Make a request for delete the instance of recipe
        res = self.client.delete(recipe_detail_url(recipe.id))

        # Test the request end successfully
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        # Test to get recipe instance before created
        self.assertFalse(Recipe.objects.filter(id=recipe.id))

    def test_change_user_returns_error(self):
        """
        Test changing recipe's user returns an error.
        """

        # Create a new recipe for test
        recipe = create_recipe(user=self.user)

        # Create a new user to use change
        new_user = get_user_model().objects.create_user(
            email='new_user@example.com',
            password='testpass123'
        )

        # Get detail URL
        url = recipe_detail_url(recipe.id)

        # Create a payload contains new user
        payload = {
            'user': new_user.id
        }

        # Test changing user
        self.client.patch(url, payload)

        # Reload recipe
        recipe.refresh_from_db()

        self.assertEqual(recipe.user, self.user)

    def test_delete_another_user_recipe(self):
        """
        Test delete another user's recipe.
        """

        # Create a new user
        new_user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        # Create a new recipe with new user
        recipe = create_recipe(user=new_user)

        # Get detail URL for created recipe
        url = recipe_detail_url(recipe.id)

        # Make a request for deletion with another user
        res = self.client.delete(url)

        # Test content didn't deleted
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Test data still be there
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_tags(self):
        """
        Test creation recipe with tags
        """

        payload = {
            'title': 'Test recipe for tags',
            'time_minutes': 16,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }

        # Make a request with existing tag name
        res = self.client.post(RECIPES_URL, payload, format='json')

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Test recipes
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        # Test tag names
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """
        Test creating a recipe with existing tags
        """
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 16,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }

        # Make a request with existing tag name
        res = self.client.post(RECIPES_URL, payload, format='json')

        # Test status code of POST request
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Test recipes count
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        # Test tag count
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        # Test tags contain tag_indian
        self.assertIn(tag_indian, recipe.tags.all())

        # Test tag names
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user).exists()
            self.assertTrue(exists)

    def create_tag_on_update(self):
        """
        Test creating tag when updating a recipe.
        """

        # Create a recipe for testing
        recipe = create_recipe(user=self.user)

        # Create a payload for new tags
        payload = {
            'tags': [{'name': 'Lunch'}]
        }

        # Get detail URL
        url = recipe_detail_url(recipe.id)

        # Make a request for update
        res = self.client.patch(url, payload, format='json')

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Get the new tag
        new_tag = Tag.objects.get(user=self.user, name='Lunch')

        # Test recipe tags contain new tag
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """
        Test assigning an existing tag when updating a recipe.
        """

        # Create a tag
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {'tags': [{'name': 'Lunch'}]}

        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """
        Test clear recipe tags.
        """
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = recipe_detail_url(recipe.id)

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.all().count(), 0)

    def test_create_recipe_with_ingredients(self):
        """
        Test create recipe with ingredients.
        """
        payload = {
            'title': 'Sample recipe title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Sample description',
            'link': 'https://example.com/recipe.pdf',
            'ingredients': [
                {'name': 'Ingredient 1'},
                {'name': 'Ingredient 2'}
            ]
        }

        # Make a POST request
        res = self.client.post(RECIPES_URL, payload, format='json')

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Test ingredients added to recipe when creation
        recipe = Recipe.objects.filter(user=self.user)[0]
        for ingredient_data in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient_data['name']).exists()
            self.assertTrue(exists)

    def test_update_ingredients_on_update_recipe(self):
        """
        Test updating ingredients of recipe when update the recipe.
        """
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [{'name': 'Salt'}, {'name': 'Pepper'}]
        }

        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        for ingredient_data in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient_data['name']).exists()
            self.assertTrue(exists)

    def test_clear_ingredients(self):
        """
        Test clear ingredients of recipe.
        """
        recipe = create_recipe(user=self.user)
        ingredient1 = Ingredient.objects.create(user=self.user, name='Ingredient 1')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Ingredient 2')

        recipe.ingredients.add(ingredient1)
        recipe.ingredients.add(ingredient2)

        payload = {'ingredients': []}

        url = recipe_detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)
