from django.core.management.base import BaseCommand
from django.db import transaction
from taggit.models import Tag
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix tag slug conflicts by ensuring unique slugs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write('Checking for tag slug conflicts...')
        
        # Get all tags
        all_tags = Tag.objects.all().order_by('name')
        conflicts_found = 0
        fixed_count = 0
        
        for tag in all_tags:
            original_slug = tag.slug
            expected_slug = slugify(tag.name)
            
            if original_slug != expected_slug:
                conflicts_found += 1
                self.stdout.write(f'  Found conflict: "{tag.name}" has slug "{original_slug}" but should be "{expected_slug}"')
                
                if not dry_run:
                    try:
                        # Check if the expected slug already exists
                        existing_tag = Tag.objects.filter(slug=expected_slug).exclude(pk=tag.pk).first()
                        
                        if existing_tag:
                            # Generate a unique slug by adding a number
                            counter = 1
                            new_slug = f"{expected_slug}-{counter}"
                            while Tag.objects.filter(slug=new_slug).exclude(pk=tag.pk).exists():
                                counter += 1
                                new_slug = f"{expected_slug}-{counter}"
                            
                            tag.slug = new_slug
                            self.stdout.write(f'    Fixed: "{tag.name}" now has slug "{new_slug}" (conflict with existing tag)')
                        else:
                            tag.slug = expected_slug
                            self.stdout.write(f'    Fixed: "{tag.name}" now has slug "{expected_slug}"')
                        
                        tag.save()
                        fixed_count += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    Error fixing tag "{tag.name}": {e}'))
        
        if conflicts_found == 0:
            self.stdout.write(self.style.SUCCESS('No tag slug conflicts found!'))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'Found {conflicts_found} conflicts (dry run mode)'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} out of {conflicts_found} conflicts'))
        
        # Also check for duplicate names (case-insensitive)
        self.stdout.write('\nChecking for duplicate tag names...')
        duplicate_names = {}
        
        for tag in all_tags:
            name_lower = tag.name.lower()
            if name_lower not in duplicate_names:
                duplicate_names[name_lower] = [tag]
            else:
                duplicate_names[name_lower].append(tag)
        
        duplicate_count = 0
        for name_lower, tags in duplicate_names.items():
            if len(tags) > 1:
                duplicate_count += 1
                self.stdout.write(f'  Found duplicate names: {[tag.name for tag in tags]}')
                
                if not dry_run:
                    try:
                        # Keep the first tag, merge others into it
                        primary_tag = tags[0]
                        tags_to_merge = tags[1:]
                        
                        for tag_to_merge in tags_to_merge:
                            # Update all posts that use this tag
                            for post in tag_to_merge.taggit_taggeditem_items.all():
                                # Add the primary tag if it's not already there
                                if not post.content_object.tags.filter(pk=primary_tag.pk).exists():
                                    post.content_object.tags.add(primary_tag)
                            
                            # Remove the duplicate tag
                            tag_to_merge.delete()
                            self.stdout.write(f'    Merged "{tag_to_merge.name}" into "{primary_tag.name}"')
                        
                        fixed_count += 1
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    Error merging tags: {e}'))
        
        if duplicate_count == 0:
            self.stdout.write(self.style.SUCCESS('No duplicate tag names found!'))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'Found {duplicate_count} duplicate names (dry run mode)'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} duplicate name issues'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\nTag conflicts have been resolved!'))
        else:
            self.stdout.write(self.style.WARNING('\nRun without --dry-run to apply these fixes'))
