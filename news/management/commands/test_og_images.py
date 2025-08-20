from django.core.management.base import BaseCommand
from django.conf import settings
from news.models import Post
from django.template.loader import render_to_string
from django.test import RequestFactory

class Command(BaseCommand):
    help = 'Test Open Graph image URLs for posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--post-id',
            type=int,
            help='Test specific post ID',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Test all published posts',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Testing Open Graph Image URLs...\n')
        )

        # Create a mock request for testing
        class MockRequest:
            def __init__(self):
                self.scheme = 'https'
                self.get_host = lambda: 'realnaijagist.com'
        
        request = MockRequest()

        if options['post_id']:
            try:
                post = Post.objects.get(id=options['post_id'])
                self.test_post_og_image(post, request)
            except Post.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Post with ID {options["post_id"]} not found')
                )
        elif options['all']:
            posts = Post.objects.filter(status=Post.PostStatus.PUBLISHED)[:5]
            for post in posts:
                self.test_post_og_image(post, request)
        else:
            # Test a sample post
            try:
                post = Post.objects.filter(status=Post.PostStatus.PUBLISHED).first()
                if post:
                    self.test_post_og_image(post, request)
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️  No published posts found')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error: {e}')
                )

    def test_post_og_image(self, post, request):
        self.stdout.write(f'\n📝 Post: {post.title}')
        self.stdout.write(f'   ID: {post.id}')
        self.stdout.write(f'   Status: {post.status}')
        
        # Test image URL generation
        image_url = post.get_image_url()
        self.stdout.write(f'   Raw Image URL: {image_url}')
        
        if image_url:
            # Test absolute URL generation
            from news.templatetags.post_filters import absolute_url
            absolute_image_url = absolute_url(image_url, request)
            self.stdout.write(f'   Absolute Image URL: {absolute_image_url}')
            
            # Test if URL is accessible
            if absolute_image_url.startswith('http'):
                self.stdout.write(f'   ✅ Valid HTTP URL')
            else:
                self.stdout.write(f'   ⚠️  Not a valid HTTP URL')
        else:
            self.stdout.write(f'   ⚠️  No image URL generated')
        
        # Test fallback image
        fallback_url = f"{request.scheme}://{request.get_host()}/static/images/og-image.jpg"
        self.stdout.write(f'   Fallback Image: {fallback_url}')
        
        # Test template rendering
        try:
            context = {
                'post': post,
                'request': request,
            }
            rendered = render_to_string('post_detail.html', context)
            
            # Extract OG image from rendered HTML
            if 'og:image' in rendered:
                self.stdout.write(f'   ✅ OG image meta tag found in template')
            else:
                self.stdout.write(f'   ❌ OG image meta tag NOT found in template')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Template rendering error: {e}')
        
        self.stdout.write('   ' + '─' * 50)
