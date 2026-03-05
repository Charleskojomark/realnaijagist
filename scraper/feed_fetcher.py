import feedparser
import requests
import re
import logging
import trafilatura
import cloudscraper
from bs4 import BeautifulSoup
from django.utils import timezone
from datetime import datetime
from email.utils import parsedate_to_datetime

from django.core.files.base import ContentFile
from cloudinary.uploader import upload as cloudinary_upload

from news.models import Post, Category
from scraper.models import NewsSource, ScrapedArticle

logger = logging.getLogger(__name__)

class FeedFetcher:
    def __init__(self, source):
        self.source = source
        self.headers = {
            'User-Agent': 'RealNaijaGistBot/1.0 (+http://realnaijagist.com)'
        }

    def fetch(self, limit=10, dry_run=False, auto_publish=False):
        """Fetch and process articles from the source RSS feed."""
        if not dry_run:
            self.source.last_fetched = timezone.now()
            self.source.save(update_fields=['last_fetched'])

        logger.info(f"Fetching RSS feed for {self.source.name} from {self.source.rss_url}")
        
        try:
            # Use requests with a browser User-Agent to bypass basic anti-bot blocks
            response = requests.get(self.source.rss_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as e:
            logger.error(f"Failed to fetch feed from {self.source.name}: {e}")
            return {'added': 0, 'existing': 0, 'failed': 0, 'articles': []}
        
        if getattr(feed, 'bozo', False) and getattr(feed, 'bozo_exception', None):
            logger.warning(f"Warning parsing feed from {self.source.name}: {feed.bozo_exception}")

        processed = 0
        results = {'added': 0, 'existing': 0, 'failed': 0, 'articles': []}

        for entry in feed.entries:
            if processed >= limit:
                break
                
            original_url = getattr(entry, 'link', None)
            if not original_url:
                continue

            # Check if this article was already scraped
            if ScrapedArticle.objects.filter(original_url=original_url).exists():
                results['existing'] += 1
                continue

            title = getattr(entry, 'title', '').strip()
            summary = self._extract_summary(entry)
            image_url = self._extract_image(entry)
            pub_date = self._extract_pub_date(entry)
            
            full_content = self._fetch_full_article_content(original_url)

            results['articles'].append({
                'title': title,
                'url': original_url,
                'image_url': image_url,
                'pub_date': pub_date
            })

            if not dry_run:
                try:
                    self._create_article(title, original_url, summary, full_content, image_url, pub_date, auto_publish)
                    results['added'] += 1
                except Exception as e:
                    logger.exception(f"Failed to process article {title}: {e}")
                    # Log the failure in ScrapedArticle
                    ScrapedArticle.objects.create(
                        source=self.source,
                        original_url=original_url,
                        original_title=title,
                        status=ScrapedArticle.Status.FAILED,
                        error_log=str(e),
                        image_url=image_url or ''
                    )
                    results['failed'] += 1

            processed += 1

        return results

    def _extract_summary(self, entry):
        """Extract a clean summary from the RSS entry."""
        # Try different summary fields provided by feeds
        raw_summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
        
        # Clean HTML tags
        clean_text = re.sub('<[^<]+?>', '', raw_summary)
        # Decode entities and strip whitespace
        import html
        clean_text = html.unescape(clean_text).strip()
        
        # Limit to ~300 chars for excerpt
        if len(clean_text) > 300:
            clean_text = clean_text[:297] + '...'
            
        return clean_text

    def _fetch_full_article_content(self, url):
        """Fetch and extract the full article content from the source URL using Trafilatura."""
        try:
            # Use Cloudscraper to bypass Cloudflare/WAF anti-bot protections
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            response = scraper.get(url, timeout=15)
            response.raise_for_status()

            # First try with Trafilatura for precise extraction
            content = trafilatura.extract(
                response.text, 
                include_images=False,
                include_links=True,
                favor_precision=True,
                output_format="html"
            )
            
            if content and len(re.sub('<[^<]+?>', '', content)) > 200:
                return content
            
            # Fallback to BeautifulSoup if Trafilatura fails
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common article containers
            selectors = [
                'article',
                '.article-body',
                '.article-content',
                '.entry-content',
                '.post-content',
                '.post-body',
                '.story-content',
            ]
            
            article_body = None
            for selector in selectors:
                body = soup.select_one(selector)
                if body:
                    article_body = body
                    break
                    
            if not article_body:
                containers = soup.find_all(['div', 'section', 'main'])
                best_container = None
                max_paragraphs = 0
                for container in containers:
                    paragraphs = container.find_all('p', recursive=False)
                    if len(paragraphs) > max_paragraphs:
                        max_paragraphs = len(paragraphs)
                        best_container = container
                if best_container and max_paragraphs >= 2:
                    article_body = best_container
                    
            if article_body:
                # Clean up unwanted elements
                unwanted = [
                    "script", "style", "nav", "footer", "header", "aside", 
                    ".social-share", ".related-posts", ".advertisement", 
                    ".comments", ".newsletter-signup"
                ]
                for element in article_body.select(", ".join(unwanted)):
                    element.decompose()
                    
                paragraphs = article_body.find_all('p')
                if paragraphs:
                    content = "".join([str(p) for p in paragraphs if p.text.strip()])
                    if len(re.sub('<[^<]+?>', '', content)) > 200:
                        return content
                        
        except Exception as e:
            logger.warning(f"Failed to fetch full content from {url}: {e}")
            
        return None

    def _extract_image(self, entry):
        """Extract the best image URL from the RSS entry."""
        # 1. Check media:content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if 'url' in media and media.get('medium') == 'image':
                    return media['url']

        # 2. Check enclosures
        if hasattr(entry, 'enclosures'):
            for enc in entry.enclosures:
                if 'type' in enc and enc['type'].startswith('image/'):
                    return enc['href']

        # 3. Check for <img> in summary/description
        raw_content = getattr(entry, 'content', [{'value': ''}])[0].get('value', '')
        raw_summary = getattr(entry, 'summary', '')
        
        for html_content in [raw_content, raw_summary]:
            if html_content and '<img' in html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    return img['src']

        return None

    def _extract_pub_date(self, entry):
        """Extract publication date as timezone-aware datetime."""
        if hasattr(entry, 'published'):
            try:
                return parsedate_to_datetime(entry.published)
            except Exception:
                pass
        return timezone.now()

    def _create_article(self, title, original_url, summary, full_content, image_url, pub_date, auto_publish):
        """Create the ScrapedArticle, download image, and create the Post."""
        
        from django.utils.text import slugify
        try:
            from django.contrib.auth.models import User
            # Try to get an author for scraped posts, default to the first superuser
            author = User.objects.filter(is_superuser=True).first()
        except ImportError:
            author = None

        # Content is now just the extracted body
        content = full_content if full_content else f"<p>{summary}</p>"

        # Determine status
        status = Post.PostStatus.PUBLISHED if auto_publish else Post.PostStatus.DRAFT

        # Create basic post
        slug_base = slugify(title)
        slug = slug_base
        counter = 1
        while Post.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{counter}"
            counter += 1

        post = Post(
            title=title,
            slug=slug,
            content=content,
            excerpt=summary,
            status=status,
            category=self.source.default_category,
            author=author,
            created_at=pub_date,
            published_at=pub_date if auto_publish else None,
            source_url=original_url,
            source_name=self.source.name,
            is_aggregated=True
        )

        # Handle image download and Cloudinary upload
        if image_url:
            try:
                # We need to upload it directly to Cloudinary or via CloudinaryField
                # First let's check if we can just set the cdn_image_url
                # Wait, cdn_image_url is exactly for this!
                post.cdn_image_url = image_url
            except Exception as e:
                logger.error(f"Error handling image {image_url}: {e}")

        # Save post
        post.save()

        # Handle featured -> CarouselSlide
        if self.source.is_featured and auto_publish:
            from news.models import CarouselSlide
            try:
                slide = CarouselSlide(
                    title=title,
                    subtitle=summary,
                    author=author,
                    is_active=True,
                    scraped_image_url=post.cdn_image_url if post.cdn_image_url else None,
                    post=post
                )
                slide.save()
            except Exception as e:
                logger.error(f"Error creating carousel slide: {e}")

        # Record successful scrape
        ScrapedArticle.objects.create(
            source=self.source,
            original_url=original_url,
            original_title=title,
            post=post,
            status=ScrapedArticle.Status.PUBLISHED if auto_publish else ScrapedArticle.Status.PENDING,
            image_url=image_url or ''
        )
