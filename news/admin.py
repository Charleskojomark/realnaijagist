from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post, CarouselSlide, Comment, NewsletterSubscriber, PostView, Video


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    fields = ('author_name', 'author_email', 'content', 'is_approved', 'created_at')
    readonly_fields = ('created_at',)


class CarouselSlideInline(admin.StackedInline):
    model = CarouselSlide
    extra = 1
    fields = ('title', 'subtitle', 'description', 'image', 'image_webp', 'cdn_image_url', 'image_alt_text', 'is_active', 'order', 'featured_until', 'responsive_images')
    prepopulated_fields = {'image_alt_text': ('title',)}
    readonly_fields = ('responsive_images',)

    def responsive_images(self, obj):
        """Display responsive image URLs in admin"""
        images = obj.get_responsive_images()
        if not images:
            return "No images available"
        html = ""
        for size, url in images.items():
            html += f"<p><strong>{size.title()}:</strong> <a href='{url}' target='_blank'>{url}</a></p>"
        return format_html(html)
    responsive_images.short_description = "Responsive Images"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'status', 'views', 'likes', 'is_trending', 'created_at')
    list_filter = ('status', 'category', 'author', 'is_trending', 'created_at')
    search_fields = ('title', 'content', 'excerpt', 'meta_keywords')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    inlines = [CommentInline]
    list_editable = ('status', 'is_trending')
    actions = ['make_published', 'make_draft']
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'status', 'excerpt', 'category', 'author', 'tags')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords')
        }),
        ('Images', {
            'fields': ('featured_image', 'featured_image_webp', 'cdn_image_url', 'image_alt_text', 'responsive_images')
        }),
        ('Video', {
            'fields': ('featured_video', 'video_thumbnail', 'video_duration', 'video_embed_url', 'is_video_post', 'video_info')
        }),
        ('Analytics', {
            'fields': ('views', 'likes', 'shares', 'is_trending')
        }),
    )
    readonly_fields = ('responsive_images', 'video_info')

    def responsive_images(self, obj):
        """Display responsive image URLs in admin"""
        images = obj.get_responsive_images()
        if not images:
            return "No images available"
        html = ""
        for size, url in images.items():
            html += f"<p><strong>{size.title()}:</strong> <a href='{url}' target='_blank'>{url}</a></p>"
        return format_html(html)
    responsive_images.short_description = "Responsive Images"
    
    def video_info(self, obj):
        """Display video information in admin"""
        if not obj.has_video_content():
            return "No video content"
        
        html = ""
        if obj.featured_video:
            html += f"<p><strong>Video:</strong> <a href='{obj.featured_video.url}' target='_blank'>View Video</a></p>"
        if obj.video_embed_url:
            html += f"<p><strong>Embed URL:</strong> <a href='{obj.video_embed_url}' target='_blank'>{obj.video_embed_url}</a></p>"
        if obj.video_duration:
            html += f"<p><strong>Duration:</strong> {obj.get_video_duration_formatted()}</p>"
        if obj.is_video_post:
            html += "<p><strong>Type:</strong> <span style='color: green;'>Video Post</span></p>"
        
        return format_html(html)
    video_info.short_description = "Video Information"

    def make_published(self, request, queryset):
        queryset.update(status=Post.PostStatus.PUBLISHED)
        self.message_user(request, "Selected posts have been published.")
    make_published.short_description = "Mark selected posts as published"

    def make_draft(self, request, queryset):
        queryset.update(status=Post.PostStatus.DRAFT)
        self.message_user(request, "Selected posts have been set to draft.")
    make_draft.short_description = "Mark selected posts as draft"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'post', 'duration', 'format', 'is_external', 'created_at')
    list_filter = ('format', 'created_at')
    search_fields = ('title', 'description', 'post__title')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'post')
        }),
        ('Video File', {
            'fields': ('video_file', 'thumbnail', 'duration', 'file_size', 'resolution', 'format')
        }),
        ('External Video', {
            'fields': ('external_url', 'embed_code'),
            'description': 'Use these fields for YouTube/Vimeo videos'
        }),
    )
    readonly_fields = ('is_external',)
    
    def is_external(self, obj):
        return obj.is_external()
    is_external.boolean = True
    is_external.short_description = 'External Video'


@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'featured_until', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description', 'post__title')
    prepopulated_fields = {'image_alt_text': ('title',)}
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'description', 'is_active', 'order', 'featured_until')
        }),
        ('Images', {
            'fields': ('image', 'image_webp', 'cdn_image_url', 'image_alt_text', 'responsive_images')
        }),
    )
    readonly_fields = ('responsive_images',)

    def responsive_images(self, obj):
        """Display responsive image URLs in admin"""
        images = obj.get_responsive_images()
        if not images:
            return "No images available"
        html = ""
        for size, url in images.items():
            html += f"<p><strong>{size.title()}:</strong> <a href='{url}' target='_blank'>{url}</a></p>"
        return format_html(html)
    responsive_images.short_description = "Responsive Images"



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at', 'post')
    search_fields = ('author', 'content', 'post__title')
    list_editable = ('is_approved',)
    date_hierarchy = 'created_at'


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'first_name')
    date_hierarchy = 'subscribed_at'
    actions = ['unsubscribe']

    def unsubscribe(self, request, queryset):
        for subscriber in queryset:
            subscriber.unsubscribe()
        self.message_user(request, "Selected subscribers have been unsubscribed.")
    unsubscribe.short_description = "Unsubscribe selected subscribers"


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'ip_address', 'user', 'viewed_at')
    list_filter = ('viewed_at', 'post')
    search_fields = ('post__title', 'ip_address', 'user__username')
    date_hierarchy = 'viewed_at'
    readonly_fields = ('user_agent', 'referrer', 'viewed_at')