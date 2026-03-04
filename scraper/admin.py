from django.contrib import admin
from django.utils.html import format_html
from .models import NewsSource, ScrapedArticle

@admin.action(description="Force fetch selected sources now")
def force_fetch_sources(modeladmin, request, queryset):
    from django.core.management import call_command
    import io
    
    out = io.StringIO()
    for source in queryset:
        call_command('fetch_news', source=source.name, force=True, publish=True, stdout=out)
    
    modeladmin.message_user(request, f"Fetch complete. Output: {out.getvalue()}")


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'is_featured', 'default_category', 'last_fetched')
    list_filter = ('is_active', 'is_featured', 'default_category')
    search_fields = ('name', 'rss_url', 'site_url')
    actions = [force_fetch_sources]


@admin.register(ScrapedArticle)
class ScrapedArticleAdmin(admin.ModelAdmin):
    list_display = ('original_title', 'source_name', 'status', 'fetched_at', 'post_link')
    list_filter = ('status', 'source', 'fetched_at')
    search_fields = ('original_title', 'original_url', 'error_log')
    readonly_fields = ('fetched_at',)
    
    def source_name(self, obj):
        return obj.source.name
    source_name.short_description = 'Source'
    
    def post_link(self, obj):
        if obj.post:
            from django.urls import reverse
            url = reverse('admin:news_post_change', args=[obj.post.id])
            return format_html('<a href="{}">View Post</a>', url)
        return "-"
    post_link.short_description = 'Post'
