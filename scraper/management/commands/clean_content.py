import re
from django.core.management.base import BaseCommand
from news.models import Post


# Patterns to strip from article body content
BAD_PATTERNS = [
    # Template tags that were accidentally stored in DB
    r'\{\{\s*post\.attribution_text_source\s*\}\}',
    r'\{\{\s*post\.source_name\s*\|\s*default:[^}]+\}\}',
    # Attribution lines that were hardcoded into content
    r'This article originally appeared on\s+\{\{[^}]+\}\}\.',
    r'This article originally appeared on\s+\{\{[^}]+\}\}',
    # Common Vanguard/Punch boilerplate appended in RSS
    r'The post .+ appeared first on [^<]+\.',
    r'This article originally appeared on .+\.(</p>)?',
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in BAD_PATTERNS]


def clean_content(content):
    if not content:
        return content
    for pattern in COMPILED:
        content = pattern.sub('', content)
    # Remove empty <p> tags left behind
    content = re.sub(r'<p>\s*</p>', '', content)
    return content.strip()


class Command(BaseCommand):
    help = 'Removes accidentally stored raw template tags from post content'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        dirty_posts = Post.objects.filter(
            is_aggregated=True,
            content__icontains='{{ post.'
        )

        count = dirty_posts.count()
        self.stdout.write(f"Found {count} posts with raw template tags in content.")

        fixed = 0
        for post in dirty_posts:
            new_content = clean_content(post.content)
            if new_content != post.content:
                if not dry_run:
                    post.content = new_content
                    post.save(update_fields=['content'])
                fixed += 1
                self.stdout.write(f"  {'[DRY-RUN] Would fix' if dry_run else 'Fixed'}: {post.title[:60]}")

        self.stdout.write(self.style.SUCCESS(
            f"\n{'[DRY-RUN] ' if dry_run else ''}Cleaned {fixed} posts."
        ))
