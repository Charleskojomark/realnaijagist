from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "RealNaijaGist Admin"
admin.site.site_title = "RealNaijaGist Admin"
admin.site.index_title = "Welcome to RealNaijaGist Admin"

urlpatterns = [
    path('secure-admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('news.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)