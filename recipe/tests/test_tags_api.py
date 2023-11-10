"""
Test for the tags API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpass123'):
    """
    Create and return a user.
    """
    return get_user_model().objects.create_user(email, password)


class PublicTagTests(TestCase):
    """
    Test unauthenticated API requests.
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test auth is required for retrieving tags.
        """
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """
    test authenticated tag API requests.
    """

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_tags(self):
        """
        Test retrieving a list of tags.
        """
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        # make a request to retrieve all tags
        res = self.client.get(TAGS_URL)

        # Test status code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Test data equals serializer data
        self.assertEqual(
            res.data,
            TagSerializer(Tag.objects.filter(user=self.user).order_by('-name'), many=True).data
        )

    def test_retrieve_tag(self):
        """
        Test retrieve a tag
        """
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Dessert')

        # Make a request for retrieve tag1
        url = detail_url(tag1.id)
        res = self.client.get(url)

        # Test response code
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Test compare response data with serializer data
        self.assertEqual(res.data, TagSerializer(tag1).data)

    def test_partial_update(self):
        """
        Test partial update a tag
        """

        # Create tag object
        tag = Tag.objects.create(user=self.user, name='Vegan')

        # Try to update
        payload = {
            'name': 'New tag name'
        }
        res = self.client.patch(detail_url(tag.id), payload)

        # Test partial update is successful
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_full_update(self):
        """
        Test full update a tag
        """

        # Create a tag
        tag = Tag.objects.create(user=self.user, name='Vegan')

        # Try to update
        payload = {
            'name': 'New tag name',
            'user': self.user.id
        }
        res = self.client.put(detail_url(tag.id), payload)

        # Test full update is successful with original user
        tag.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user.id, self.user.id)

    def test_change_tag_user(self):
        """
        Test change tag user returns error
        """

        new_user = create_user('test@example.com', 'testpass123')
        tag = Tag.objects.create(user=self.user, name='test tag name')

        url = detail_url(tag.id)
        self.client.patch(url, {'user': new_user.id})

        tag.refresh_from_db()
        self.assertEqual(tag.user, self.user)

    def test_tag_delete(self):
        """
        Test tag delete
        """

        # Create a tag
        tag = Tag.objects.create(user=self.user, name='test name')

        # Create detail URL
        url = detail_url(tag.id)

        # Make a request to delete this tag
        res = self.client.delete(url)

        # Test response code
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        # Try to get access this tag on DB
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_retrieve_tags_limited_user(self):
        """
        Test retrieve tags limited to a user
        """

        # Create a User and tag
        user2 = create_user('user2@example.com', 'testpass123')
        Tag.objects.create(user=user2, name='User 2 tag')

        # Create another tag to get with API
        tag = Tag.objects.create(user=self.user, name='tag name')

        # Make a request to fetch all tags
        res = self.client.get(TAGS_URL)

        # Test tag name and user
        self.assertEqual(res.data[0]['name'], 'tag name')
        self.assertEqual(res.data[0]['id'], tag.id)
        self.assertEqual(len(res.data), 1)

