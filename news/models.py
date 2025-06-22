from django.db import models
from django.urls import reverse
from django.db.models import F
from django_ckeditor_5.fields import CKEditor5Field
from django.core.files.storage import default_storage
from django.utils import timezone
from taggit.managers import TaggableManager 
from cloudinary.models import CloudinaryField 


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'


class Post(models.Model):
    class PostStatus(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, db_index=True)
    content = CKEditor5Field(config_name='default')
    status = models.CharField(
        max_length=20, 
        choices=PostStatus.choices, 
        default=PostStatus.DRAFT,
        db_index=True
    )
    excerpt = models.TextField(max_length=500, blank=True)
    
    # SEO fields
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Images with CDN support
    featured_image = CloudinaryField('image', blank=True, null=True) 
    featured_image_webp = models.ImageField(upload_to='blog/images/webp/', blank=True, null=True, help_text="WebP version for faster loading")
    image_alt_text = models.CharField(max_length=100, blank=True)
    
    # Optional: Direct CDN URL override
    cdn_image_url = models.URLField(max_length=500, blank=True, help_text="Direct CDN URL (overrides uploaded image)")
    
    # Relationships
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='posts')
    tags = TaggableManager(blank=True) 
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    # Analytics
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    
    # Editorial flags
    is_trending = models.BooleanField(default=False)  # Currently trending

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:post_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Thread-safe way to increment view count"""
        Post.objects.filter(pk=self.pk).update(views=F('views') + 1)
        self.refresh_from_db(fields=['views'])

    def is_published(self):
        return self.status == self.PostStatus.PUBLISHED

    def get_image_url(self, size='original'):
        """Get optimized image URL with CDN support"""
        if self.cdn_image_url:
            return self.cdn_image_url
        
        if size == 'webp' and self.featured_image_webp:
            return self.featured_image_webp.url
        elif self.featured_image:
            return self.featured_image.url
        return None

    def get_responsive_images(self):
        """Get multiple image sizes for responsive design"""
        base_url = self.get_image_url()
        if not base_url:
            return {}
        
        # If using a CDN service like Cloudinary, you can generate different sizes
        return {
            'thumbnail': f"{base_url}?w=300&h=200&c=fill",  # Adjust based on your CDN
            'medium': f"{base_url}?w=600&h=400&c=fill",
            'large': f"{base_url}?w=1200&h=800&c=fill",
            'original': base_url
        }
        """Return excerpt or truncated content if excerpt is empty"""
        if self.excerpt:
            return self.excerpt
        # Remove HTML tags for excerpt
        import re
        clean_content = re.sub('<[^<]+?>', '', self.content)
        return clean_content[:200] + '...' if len(clean_content) > 200 else clean_content

    def get_popularity_score(self):
        """Calculate popularity based on multiple factors"""
        # Weight different engagement types
        return (self.views * 1) + (self.likes * 5) + (self.shares * 10) + (self.comments.count() * 8)

    @classmethod
    def get_popular_posts(cls, limit=5, days=30):
        """Get most popular posts in the last N days"""
        from django.utils import timezone
        from datetime import timedelta
        
        since_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            status=cls.PostStatus.PUBLISHED,
            created_at__gte=since_date
        ).order_by('-views', '-likes')[:limit]

    

    @classmethod
    def get_trending_posts(cls, limit=5):
        """Get trending posts"""
        return cls.objects.filter(
            status=cls.PostStatus.PUBLISHED,
            is_trending=True
        ).order_by('-created_at')[:limit]

    def save(self, *args, **kwargs):
        """Auto-set published_at when status changes to published"""
        if self.status == self.PostStatus.PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-views']),
        ]


from django.db import models
from django.utils import timezone

class CarouselSlide(models.Model):
    """Featured content displayed in hero carousel"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(max_length=500, blank=True)
    
    # Images with optimization
    image = models.ImageField(upload_to='carousel/')
    image_webp = models.ImageField(upload_to='carousel/webp/', blank=True, null=True)
    image_alt_text = models.CharField(max_length=100, blank=True)
    
    # Display settings
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    # Auto-expiry for time-sensitive features
    featured_until = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (Order: {self.order})"

    def get_image_url(self, size='original'):
        """Get optimized image URL"""
        if size == 'webp' and self.image_webp:
            return self.image_webp.url
        elif self.image:
            return self.image.url
        return None

    def get_responsive_images(self):
        """Get multiple image sizes for responsive design"""
        base_url = self.get_image_url()
        if not base_url:
            return {}
        return {
            'mobile': f"{base_url}?w=480&h=270&c=fill&f=webp",
            'tablet': f"{base_url}?w=768&h=432&c=fill&f=webp", 
            'desktop': f"{base_url}?w=1200&h=675&c=fill&f=webp",
            'original': base_url
        }

    def is_currently_active(self):
        """Check if slide is active and not expired"""
        if not self.is_active:
            return False
        if self.featured_until:
            return timezone.now() <= self.featured_until
        return True

    def save(self, *args, **kwargs):
        """Auto-populate subtitle and image_alt_text"""
        if not self.subtitle and self.description:
            self.subtitle = self.description[:300]
        if not self.image_alt_text:
            self.image_alt_text = self.title
        super().save(*args, **kwargs)

    @classmethod
    def get_active_slides(cls):
        """Get currently active carousel slides"""
        return cls.objects.filter(
            is_active=True,
        ).filter(
            models.Q(featured_until__isnull=True) | 
            models.Q(featured_until__gt=timezone.now())
        ).order_by('order', '-created_at')

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Carousel Slide"
        verbose_name_plural = "Carousel Slides"
        



class Comment(models.Model):
    """Comments system for posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    content = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.author_name} on {self.post.title}'

    class Meta:
        ordering = ['-created_at']


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    
    # Optional subscriber details
    first_name = models.CharField(max_length=50, blank=True)
    preferences = models.JSONField(default=dict, blank=True)  # Store subscription preferences

    def __str__(self):
        return self.email

    def unsubscribe(self):
        """Mark subscriber as inactive"""
        from django.utils import timezone
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-subscribed_at']


class PostView(models.Model):
    """Track detailed view analytics"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_views')
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.post.title} - {self.viewed_at}'

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['post', '-viewed_at']),
            models.Index(fields=['ip_address', '-viewed_at']),
        ]