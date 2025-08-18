"""
Tests for the news application
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Category, Post, CarouselSlide
from taggit.models import Tag


class NewsViewsTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            description='Test category description'
        )
        
        # Create test post
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='This is a test post content.',
            excerpt='Test excerpt',
            status=Post.PostStatus.PUBLISHED,
            category=self.category,
            author=self.user,
            published_at=timezone.now()
        )
        
        # Create test carousel slide
        self.slide = CarouselSlide.objects.create(
            title='Test Slide',
            subtitle='Test Subtitle',
            description='Test slide description',
            is_active=True,
            order=1,
            author=self.user
        )
        
        # Set up client
        self.client = Client()

    def test_home_page(self):
        """Test that home page loads correctly"""
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Test Category')

    def test_post_detail_page(self):
        """Test that post detail page loads correctly"""
        response = self.client.get(self.post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'This is a test post content.')

    def test_category_page(self):
        """Test that category page loads correctly"""
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Category')
        self.assertContains(response, 'Test Post')

    def test_search_functionality(self):
        """Test search functionality"""
        response = self.client.get(reverse('news:search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')

    def test_carousel_slides(self):
        """Test that carousel slides are displayed"""
        response = self.client.get(reverse('news:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Slide')

    def test_404_page(self):
        """Test 404 page for non-existent post"""
        response = self.client.get('/post/non-existent-post/')
        self.assertEqual(response.status_code, 404)

    def test_post_views_increment(self):
        """Test that post views increment correctly"""
        initial_views = self.post.views
        self.post.increment_views()
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, initial_views + 1)


class NewsModelsTestCase(TestCase):
    def setUp(self):
        """Set up test data for models"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_category_str_method(self):
        """Test Category __str__ method"""
        self.assertEqual(str(self.category), 'Test Category')

    def test_post_str_method(self):
        """Test Post __str__ method"""
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            category=self.category,
            author=self.user
        )
        self.assertEqual(str(post), 'Test Post')

    def test_post_status_choices(self):
        """Test Post status choices"""
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            category=self.category,
            author=self.user
        )
        self.assertIn(post.status, [choice[0] for choice in Post.PostStatus.choices])

    def test_post_get_absolute_url(self):
        """Test Post get_absolute_url method"""
        post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            category=self.category,
            author=self.user
        )
        expected_url = f'/post/{post.slug}/'
        self.assertEqual(post.get_absolute_url(), expected_url)

    def test_category_get_absolute_url(self):
        """Test Category get_absolute_url method"""
        expected_url = f'/category/{self.category.slug}/'
        self.assertEqual(self.category.get_absolute_url(), expected_url)


class NewsFormsTestCase(TestCase):
    def setUp(self):
        """Set up test data for forms"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

    def test_post_form_valid(self):
        """Test PostForm with valid data"""
        from .forms import PostForm
        
        form_data = {
            'title': 'Test Post',
            'content': 'Test content',
            'excerpt': 'Test excerpt',
            'category': self.category.id,
            'status': 'draft'
        }
        
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_post_form_invalid(self):
        """Test PostForm with invalid data"""
        from .forms import PostForm
        
        form_data = {
            'title': '',  # Required field
            'content': 'Test content',
            'category': self.category.id
        }
        
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class NewsAdminTestCase(TestCase):
    def setUp(self):
        """Set up test data for admin"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@example.com'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            content='Test content',
            category=self.category,
            author=self.admin_user
        )

    def test_admin_access(self):
        """Test that admin can access admin site"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_post_admin_list_display(self):
        """Test Post admin list display"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin:news_post_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Post')
        self.assertContains(response, 'Test Category')
