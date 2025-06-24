from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'news'
urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('category/<slug:slug>/', views.category_filter, name='category_detail'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/like/', views.like_post, name='like_post'),
    path('post/<slug:slug>/share/', views.share_post, name='share_post'),
    path('newsletter/', views.newsletter_subscribe, name='newsletter'),
    path('accounts/login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('advertise/', views.advertise, name='advertise'),
    path('write/', views.write, name='write'),
    path('carousel/<int:pk>/', views.carousel_slide_detail, name='carousel_slide_detail'),
    
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    # Admin endpoints
    path('superuser/posts/', views.post_list, name='post_list'),
    path('superuser/posts/add/', views.post_create, name='post_create'),
    path('superuser/posts/<int:pk>/edit/', views.post_update, name='post_update'),
    path('superuser/posts/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('superuser/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('superuser/category/add/', views.add_category, name='add_category'),
    path('superuser/category/edit/<int:pk>/', views.edit_category, name='edit_category'),
    path('superuser/category/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('superuser/carousel/add/', views.add_carousel_slide, name='add_carousel_slide'),
    path('superuser/carousel/edit/<int:pk>/', views.edit_carousel_slide, name='edit_carousel_slide'),
    path('superuser/carousel/delete/<int:pk>/', views.delete_carousel_slide, name='delete_carousel_slide'),
    path('superuser/subscriber/delete/<int:pk>/', views.delete_subscriber, name='delete_subscriber'),
    
    # test server error
    # path('test-500/', views.test_500, name='test_500'),
]