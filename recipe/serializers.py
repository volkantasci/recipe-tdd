"""Serializers for Recipe"""

from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient


class TagSerializer(serializers.ModelSerializer):
    """
    Tag Serializer for filter recipes
    """

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data.pop('user', None)
        tag = Tag.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        return tag

    def update(self, instance, validated_data):
        validated_data.pop('user', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


class IngredientSerializer(serializers.ModelSerializer):
    """
    Ingredient serializer for adding to recipes
    """

    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

    def create(self, validated_data):
        validated_data.pop('user', None)
        ingredient = Ingredient.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        return ingredient

    def update(self, instance, validated_data):
        validated_data.pop('user', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance


def get_or_create_tags(user, tags, recipe):
    """
    Handle getting or creating tags as needed.
    """
    for tag in tags:
        tag_obj, created = Tag.objects.get_or_create(
            user=user,
            name=tag['name']
        )
        recipe.tags.add(tag_obj)


def get_or_create_ingredients(user, ingredients, recipe):
    """
    Handle getting or creating ingredients as needed.
    """
    for ingredient in ingredients:
        ingredient_obj, created = Ingredient.objects.get_or_create(
            user=user,
            name=ingredient['name']
        )
        recipe.ingredients.add(ingredient_obj)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    def create(self, validated_data):
        """
        Create a recipe with tags
        """
        validated_data.pop('user', None)
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        auth_user = self.context['request'].user
        recipe = Recipe.objects.create(user=auth_user, **validated_data)

        get_or_create_tags(auth_user, tags, recipe)
        get_or_create_ingredients(auth_user, ingredients, recipe)

        return recipe

    def update(self, instance: Recipe, validated_data):
        """
        Update a recipe with tags
        """
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        auth_user = self.context['request'].user
        if tags is not None:
            instance.tags.clear()
            get_or_create_tags(auth_user, tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            get_or_create_ingredients(auth_user, ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


class RecipeImageSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading recipe image.
    """

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {
            'image':
                {'required': 'True'}
        }
