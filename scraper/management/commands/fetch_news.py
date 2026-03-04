from django.core.management.base import BaseCommand
from scraper.models import NewsSource
from scraper.feed_fetcher import FeedFetcher

class Command(BaseCommand):
    help = 'Fetches news from active RSS sources'

    def add_arguments(self, parser):
        parser.add_argument('--source', type=str, help='Fetch from a specific NewsSource by name')
        parser.add_argument('--limit', type=int, default=10, help='Max articles to fetch per source')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
        parser.add_argument('--publish', action='store_true', help='Auto-publish fetched articles')
        parser.add_argument('--force', action='store_true', help='Ignore fetch_interval and force fetch')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_publish = options['publish']
        limit = options['limit']
        force = options['force']
        source_name = options['source']

        sources = NewsSource.objects.filter(is_active=True)
        if source_name:
            sources = sources.filter(name__icontains=source_name)

        if not sources.exists():
            self.stdout.write(self.style.WARNING("No active news sources found."))
            return

        total_added = 0
        total_failed = 0

        for source in sources:
            if not force and not source.should_fetch() and not dry_run:
                self.stdout.write(f"Skipping {source.name} (fetched recently). Use --force to override.")
                continue

            self.stdout.write(f"Fetching {source.name}...")
            
            fetcher = FeedFetcher(source)
            results = fetcher.fetch(limit=limit, dry_run=dry_run, auto_publish=auto_publish)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Processed {source.name}: {results['added']} added, "
                    f"{results['existing']} existing, {results['failed']} failed."
                )
            )
            
            total_added += results['added']
            total_failed += results['failed']

        self.stdout.write(
            self.style.SUCCESS(
                f"\nFetch complete! Total added: {total_added}, Total failed: {total_failed}"
            )
        )
