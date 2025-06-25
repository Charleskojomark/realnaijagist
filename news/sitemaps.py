from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Post, Category, CarouselSlide

class PostSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Post.objects.filter(status=Post.PostStatus.PUBLISHED).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at or obj.created_at

    def location(self, obj):
        return obj.get_absolute_url()

    def image(self, obj):
        image_url = obj.get_image_url()
        if image_url:
            return {
                'loc': image_url,
                'title': obj.title,
                'caption': obj.image_alt_text or obj.title,
            }
        return None

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        latest_post = obj.posts.filter(status=Post.PostStatus.PUBLISHED).order_by('-updated_at').first()
        return latest_post.updated_at if latest_post else obj.created_at

class CarouselSlideSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return CarouselSlide.get_active_slides()

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.updated_at or obj.created_at

    def image(self, obj):
        image_url = obj.get_image_url()
        if image_url:
            return {
                'loc': image_url,
                'title': obj.title,
                'caption': obj.image_alt_text or obj.title,
            }
        return None

class NewsSitemap(Sitemap):
    changefreq = 'hourly'
    priority = 1.0
    protocol = 'https'

    def items(self):
        since_date = timezone.now() - timedelta(days=2)
        return Post.objects.filter(
            status=Post.PostStatus.PUBLISHED,
            published_at__gte=since_date
        ).order_by('-published_at')

    def location(self, obj):
        return obj.get_absolute_url()

    def lastmod(self, obj):
        return obj.published_at or obj.created_at

    def news(self, obj):
        return {
            'title': obj.title,
            'publication_date': obj.published_at.isoformat() if obj.published_at else obj.created_at.isoformat(),
            'publication': {
                'name': 'RealNaijaGist',
                'language': 'en',
            },
            'keywords': obj.meta_keywords or ', '.join(tag.name for tag in obj.tags.all()),
        }

class NewsSitemapIndex(Sitemap):
    def items(self):
        return ['posts', 'categories', 'carousel_slides', 'news']

    def location(self, obj):
        return reverse('django.contrib.sitemaps.views.sitemap', kwargs={'section': obj})

    def lastmod(self, obj):
        if obj == 'posts':
            post = Post.objects.filter(status=Post.PostStatus.PUBLISHED).order_by('-updated_at').first()
            return post.updated_at if post else timezone.now()
        elif obj == 'categories':
            category = Category.objects.order_by('-created_at').first()
            return category.created_at if category else timezone.now()
        elif obj == 'carousel_slides':
            slide = CarouselSlide.get_active_slides().first()
            return slide.updated_at if slide else timezone.now()
        elif obj == 'news':
            post = Post.objects.filter(status=Post.PostStatus.PUBLISHED).order_by('-published_at').first()
            return post.published_at if post else timezone.now()
        return timezone.now()