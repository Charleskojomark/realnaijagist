from rest_framework import serializers
from .models import Category, Post, CarouselSlide, Tag, Comment, NewsletterSubscriber
from django.contrib.auth.models import User


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='category-detail', lookup_field='slug')

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'url']


class TagSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='tag-detail', lookup_field='slug')

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'created_at', 'url']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(required=True)
    author_email = serializers.EmailField(required=True)
    post = serializers.SlugRelatedField(slug_field='slug', queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author_name', 'author_email', 'content', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['is_approved', 'created_at', 'updated_at']


class CarouselSlideSerializer(serializers.ModelSerializer):
    post = serializers.SlugRelatedField(slug_field='slug', queryset=Post.objects.all())
    image_url = serializers.ImageField(source='image', read_only=True)
    image_webp_url = serializers.ImageField(source='image_webp', read_only=True)
    responsive_images = serializers.DictField(read_only=True, source='get_responsive_images')
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = CarouselSlide
        fields = [
            'id', 'title', 'subtitle', 'description', 'image', 'image_url', 'image_webp', 
            'image_webp_url', 'cdn_image_url', 'image_alt_text', 'post', 'is_active', 
            'order', 'featured_until', 'is_currently_active', 'responsive_images', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'image_url', 'image_webp_url', 'responsive_images']


class PostSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_slug = serializers.SlugRelatedField(
        source='category', slug_field='slug', queryset=Category.objects.all(), write_only=True
    )
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_slugs = serializers.SlugRelatedField(
        source='tags', slug_field='slug', many=True, queryset=Tag.objects.all(), write_only=True
    )
    url = serializers.HyperlinkedIdentityField(view_name='post-detail', lookup_field='slug')
    excerpt = serializers.CharField(read_only=True, source='get_excerpt')
    popularity_score = serializers.IntegerField(read_only=True, source='get_popularity_score')
    carousel_slides = CarouselSlideSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    featured_image_url = serializers.ImageField(source='featured_image', read_only=True)
    featured_image_webp_url = serializers.ImageField(source='featured_image_webp', read_only=True)
    responsive_images = serializers.DictField(read_only=True, source='get_responsive_images')

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'status', 'excerpt', 'meta_description', 'meta_keywords',
            'featured_image', 'featured_image_url', 'featured_image_webp', 'featured_image_webp_url',
            'cdn_image_url', 'image_alt_text', 'category', 'category_slug', 'author', 'tags', 'tag_slugs',
            'created_at', 'updated_at', 'published_at', 'views', 'likes', 'shares', 'is_trending', 'url',
            'popularity_score', 'carousel_slides', 'comments', 'responsive_images'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'published_at', 'views', 'likes', 'shares', 'author',
            'featured_image_url', 'featured_image_webp_url', 'responsive_images'
        ]

    def create(self, validated_data):
        category = validated_data.pop('category')
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(category=category, **validated_data)
        post.tags.set(tags)
        return post

    def update(self, validated_data):
        category = validated_data.pop('category', None)
        tags = validated_data.pop('tags', None)
        instance = super().update(validated_data)
        if category:
            instance.category = category
        if tags is not None:
            instance.tags.set(tags)
        instance.save()
        return instance


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ['id', 'email', 'first_name', 'is_active', 'subscribed_at', 'preferences']
        read_only_fields = ['subscribed_at', 'unsubscribed_at']

    def validate_email(self, value):
        if NewsletterSubscriber.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("This email is already subscribed.")
        return value