from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Post, Category, CarouselSlide
from django.utils.text import slugify
from taggit.models import Tag

@receiver([post_save, post_delete], sender=Post)
@receiver([post_save, post_delete], sender=Category)
@receiver([post_save, post_delete], sender=CarouselSlide)
def clear_sitemap_cache(sender, instance, **kwargs):
    cache.delete_pattern('realnaijagist*')  # Clear all sitemap-related cache keys

@receiver(pre_save, sender=Tag)
def ensure_unique_tag_slug(sender, instance, **kwargs):
    """
    Ensure that tag slugs are unique by appending a number if necessary.
    This prevents the 'Duplicate entry for key slug' error.
    """
    if not instance.slug:
        # Generate slug from name
        instance.slug = slugify(instance.name)
    
    # Check if slug already exists (excluding current instance)
    if instance.pk:
        # For existing tags, exclude self from uniqueness check
        existing_tags = Tag.objects.filter(slug=instance.slug).exclude(pk=instance.pk)
    else:
        # For new tags, check all existing tags
        existing_tags = Tag.objects.filter(slug=instance.slug)
    
    if existing_tags.exists():
        # Generate unique slug by appending a number
        counter = 1
        base_slug = instance.slug
        while Tag.objects.filter(slug=f"{base_slug}-{counter}").exists():
            counter += 1
        instance.slug = f"{base_slug}-{counter}"