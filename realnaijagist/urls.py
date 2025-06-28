from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from news import views
from django.contrib.sitemaps.views import sitemap
from django.views.decorators.cache import cache_page
from django.views.static import serve
from news.sitemaps import PostSitemap, CategorySitemap, CarouselSlideSitemap, NewsSitemap
import os

sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
    'carousel_slides': CarouselSlideSitemap,
    'news': NewsSitemap,
}

admin.site.site_header = "RealNaijaGist Admin"
admin.site.site_title = "RealNaijaGist Admin"
admin.site.index_title = "Welcome to RealNaijaGist Admin"

handler404 = views.handler404
handler500 = views.handler500

urlpatterns = [
    path('secure-admin/', admin.site.urls),
    
    # This single sitemap view serves as both the index and sectioned sitemaps
    path('sitemap.xml', cache_page(60 * 60)(sitemap), {'sitemaps': sitemaps}, name='sitemap'),
    path('sitemap-<section>.xml', cache_page(60 * 60)(sitemap), {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    path('robots.txt', serve, {'document_root': settings.BASE_DIR, 'path': 'robots.txt'}),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('news.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
