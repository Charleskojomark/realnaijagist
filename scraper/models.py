from django.db import models
from django.utils import timezone

class NewsSource(models.Model):
    """Configuration for an RSS feed to aggregate news from."""
    name = models.CharField(max_length=100, help_text="e.g. Punch Nigeria")
    site_url = models.URLField(help_text="Homepage URL of the source")
    rss_url = models.URLField(unique=True, help_text="Direct URL to the RSS feed")
    
    default_category = models.ForeignKey(
        'news.Category', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='news_sources',
        help_text="Category to assign to scraped posts by default"
    )
    
    is_active = models.BooleanField(default=True, help_text="Uncheck to stop fetching from this feed")
    is_featured = models.BooleanField(default=False, help_text="If checked, scraped posts will also be added to the Homepage Carousel")
    
    fetch_interval = models.PositiveIntegerField(default=60, help_text="Minimum minutes between fetches")
    last_fetched = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
        
    def should_fetch(self):
        """Check if enough time has passed since last fetch"""
        if not self.is_active:
            return False
        if not self.last_fetched:
            return True
        time_since_fetch = timezone.now() - self.last_fetched
        return time_since_fetch.total_seconds() >= (self.fetch_interval * 60)


class ScrapedArticle(models.Model):
    """Log of every article found in the RSS feeds to prevent duplicates and track status."""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PUBLISHED = 'published', 'Published'
        FAILED = 'failed', 'Failed'
        REJECTED = 'rejected', 'Rejected'
        
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, related_name='scraped_articles')
    original_url = models.URLField(unique=True, max_length=500, db_index=True)
    original_title = models.CharField(max_length=300)
    
    post = models.ForeignKey(
        'news.Post', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='scraped_from'
    )
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    image_url = models.URLField(max_length=1000, blank=True)
    
    error_log = models.TextField(blank=True, help_text="Error details if fetching/parsing failed")
    fetched_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-fetched_at']
        
    def __str__(self):
        return self.original_title
