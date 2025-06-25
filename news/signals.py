from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Post, Category, CarouselSlide

@receiver([post_save, post_delete], sender=Post)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=CarouselSlide)
def clear_sitemap_cache(sender, instance, **kwargs):
    cache.delete_pattern('realnaijagist*')  # Clear all sitemap-related cache keys