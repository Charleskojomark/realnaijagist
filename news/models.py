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
        return reverse('news:category_detail', kwargs={'slug': self.slug})

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
    
    # Video support
    featured_video = models.FileField(upload_to='blog/videos/', blank=True, null=True, help_text="Featured video for the post")
    video_thumbnail = models.ImageField(upload_to='blog/videos/thumbnails/', blank=True, null=True, help_text="Custom thumbnail for video")
    video_duration = models.PositiveIntegerField(blank=True, null=True, help_text="Video duration in seconds")
    video_embed_url = models.URLField(max_length=500, blank=True, help_text="YouTube/Vimeo embed URL")
    is_video_post = models.BooleanField(default=False, help_text="Mark if this post is primarily a video post")
    
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

    def increment_views(self, ip_address=None, user=None, user_agent='', referrer=''):
        """Thread-safe way to increment view count and record detailed analytics"""
        Post.objects.filter(pk=self.pk).update(views=F('views') + 1)
        self.refresh_from_db(fields=['views'])
        PostView.objects.create(
            post=self,
            ip_address=ip_address or '0.0.0.0',
            user=user,
            user_agent=user_agent,
            referrer=referrer
        )

    def is_published(self):
        return self.status == self.PostStatus.PUBLISHED

    def get_image_url(self, size='original'):
        """Get optimized image URL with CDN support"""
        if self.cdn_image_url:
            return self.cdn_image_url
        
        if size == 'webp' and self.featured_image_webp:
            return self.featured_image_webp.url
        elif self.featured_image:
            try:
                return self.featured_image.url
            except Exception as e:
                # Fallback for when Cloudinary is not configured
                print(f"Error getting image URL: {e}")
                return None
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
    
    def get_preview_media(self):
        """
        Get the best available preview media for homepage/cards.
        Priority: featured_image > video_thumbnail > default_video_placeholder
        """
        # First try to get the featured image
        if self.featured_image:
            base_url = self.get_image_url()
            if base_url:
                return {
                    'type': 'image',
                    'url': f"{base_url}?w=300&h=200&c=fill",
                    'alt': self.image_alt_text or self.title,
                    'thumbnail': f"{base_url}?w=300&h=200&c=fill",
                    'medium': f"{base_url}?w=600&h=400&c=fill",
                    'large': f"{base_url}?w=1200&h=800&c=fill",
                    'original': base_url
                }
        
        # If no image, try to get video thumbnail
        if self.video_thumbnail:
            return {
                'type': 'video_thumbnail',
                'url': self.video_thumbnail.url,
                'alt': f"Video thumbnail for {self.title}",
                'thumbnail': self.video_thumbnail.url,
                'medium': self.video_thumbnail.url,
                'large': self.video_thumbnail.url,
                'original': self.video_thumbnail.url
            }
        
        # If no video thumbnail but has video content, use default video placeholder
        if self.has_video_content():
            return {
                'type': 'video_placeholder',
                'url': '/static/images/video-placeholder.svg',
                'alt': f"Video post: {self.title}",
                'thumbnail': '/static/images/video-placeholder.svg',
                'medium': '/static/images/video-placeholder.svg',
                'large': '/static/images/video-placeholder.svg',
                'original': '/static/images/video-placeholder.svg'
            }
        
        # If no media at all, use default placeholder
        return {
            'type': 'default_placeholder',
            'url': '/static/images/post-placeholder.svg',
            'alt': f"No image available for {self.title}",
            'thumbnail': '/static/images/post-placeholder.svg',
            'medium': '/static/images/post-placeholder.svg',
            'large': '/static/images/post-placeholder.svg',
            'original': '/static/images/post-placeholder.svg'
        }
    
    def get_video_url(self):
        """Get video URL with fallback to embed URL"""
        if self.featured_video:
            return self.featured_video.url
        elif self.video_embed_url:
            return self.video_embed_url
        return None
    
    def get_video_thumbnail_url(self):
        """Get video thumbnail URL with fallback to featured image"""
        if self.video_thumbnail:
            return self.video_thumbnail.url
        elif self.featured_image:
            return self.get_image_url('medium')
        return None
    
    def has_video_content(self):
        """Check if post has any video content"""
        return bool(self.featured_video or self.video_embed_url)
    
    def get_video_duration_formatted(self):
        """Get formatted video duration"""
        if not self.video_duration:
            return None
        
        minutes = self.video_duration // 60
        seconds = self.video_duration % 60
        if minutes > 0:
            return f"{minutes}:{seconds:02d}"
        return f"{seconds}s"
    
    def get_excerpt_or_truncated_content(self):
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

    def validate_tags(self):
        """Validate that all tags have valid slugs"""
        from taggit.models import Tag
        invalid_tags = []
        
        for tag in self.tags.all():
            try:
                # Check if tag slug is valid
                expected_slug = tag.slug
                if not expected_slug or len(expected_slug) > 100:
                    invalid_tags.append(tag.name)
            except Exception:
                invalid_tags.append(tag.name)
        
        return invalid_tags

    def save(self, *args, **kwargs):
        """Auto-set published_at when status changes to published"""
        if self.status == self.PostStatus.PUBLISHED and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['author', 'status']),
            models.Index(fields=['is_trending', 'created_at']),
            models.Index(fields=['is_video_post', 'created_at']),
        ]


class CarouselSlide(models.Model):
    """Featured content displayed in hero carousel"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(max_length=500, blank=True)
    
    # Images with optimization
    image = CloudinaryField('carousel', blank=True, null=True) 
    image_webp = models.ImageField(upload_to='carousel/webp/', blank=True, null=True)
    image_alt_text = models.CharField(max_length=100, blank=True)
    
    # Relationships
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='carousel_slides')
    
    # Analytics
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    
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

    def get_absolute_url(self):
        return reverse('news:carousel_slide_detail', kwargs={'pk': self.pk})

    def increment_views(self, ip_address=None, user=None, user_agent='', referrer=''):
        """Thread-safe way to increment view count and record detailed analytics"""
        CarouselSlide.objects.filter(pk=self.pk).update(views=F('views') + 1)
        self.refresh_from_db(fields=['views'])
        SlideView.objects.create(
            slide=self,
            ip_address=ip_address or '0.0.0.0',
            user=user,
            user_agent=user_agent,
            referrer=referrer
        )

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

class SlideView(models.Model):
    """Track detailed view analytics for carousel slides"""
    slide = models.ForeignKey(CarouselSlide, on_delete=models.CASCADE, related_name='slide_views')
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.slide.title} - {self.viewed_at}'

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['slide', '-viewed_at']),
            models.Index(fields=['ip_address', '-viewed_at']),
        ]        



class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='comments')  # Changed to ForeignKey to require authenticated user
    content = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'

    class Meta:
        ordering = ['-created_at']

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='user_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']  # Ensure a user can like a post only once
        indexes = [
            models.Index(fields=['post', 'user']),
        ]

class Video(models.Model):
    """Dedicated video model for better video management"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Video file (Local storage)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    
    # Video metadata
    duration = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in seconds")
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text="File size in bytes")
    resolution = models.CharField(max_length=20, blank=True, help_text="e.g., 1920x1080")
    format = models.CharField(max_length=10, blank=True, help_text="e.g., MP4, WebM")
    
    # Thumbnail
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', blank=True, null=True)
    
    # External video support
    external_url = models.URLField(blank=True, help_text="YouTube/Vimeo URL")
    embed_code = models.TextField(blank=True, help_text="HTML embed code")
    
    # Post relationship
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='videos', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_video_url(self):
        """Get video URL with fallback to external URL"""
        if self.video_file:
            return self.video_file.url
        elif self.external_url:
            return self.external_url
        return None
    
    def get_duration_formatted(self):
        """Get formatted duration"""
        if not self.duration:
            return None
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        if minutes > 0:
            return f"{minutes}:{seconds:02d}"
        return f"{seconds}s"
    
    def is_external(self):
        """Check if video is external (YouTube/Vimeo)"""
        return bool(self.external_url or self.embed_code)
    
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