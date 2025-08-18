"""
Management command to backup the database
Usage: python manage.py backup_db
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import os
import subprocess
import gzip
from pathlib import Path


class Command(BaseCommand):
    help = 'Backup the database to a compressed file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)',
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress the backup file',
        )

    def handle(self, *args, **options):
        # Create backups directory if it doesn't exist
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)

        # Generate backup filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        if options['output']:
            backup_file = Path(options['output'])
        else:
            backup_file = backup_dir / f'backup_{timestamp}.sql'

        # Get database configuration
        db_settings = settings.DATABASES['default']
        engine = db_settings['ENGINE']

        try:
            if 'sqlite' in engine:
                self.backup_sqlite(db_settings, backup_file, options['compress'])
            elif 'mysql' in engine:
                self.backup_mysql(db_settings, backup_file, options['compress'])
            elif 'postgresql' in engine:
                self.backup_postgresql(db_settings, backup_file, options['compress'])
            else:
                self.stdout.write(
                    self.style.ERROR(f'Unsupported database engine: {engine}')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f'Database backup completed: {backup_file}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )

    def backup_sqlite(self, db_settings, backup_file, compress):
        """Backup SQLite database"""
        source_db = Path(db_settings['NAME'])
        if not source_db.exists():
            raise FileNotFoundError(f"Database file not found: {source_db}")

        # Copy the database file
        import shutil
        shutil.copy2(source_db, backup_file)

        if compress:
            self.compress_file(backup_file)

    def backup_mysql(self, db_settings, backup_file, compress):
        """Backup MySQL database"""
        cmd = [
            'mysqldump',
            f'--host={db_settings["HOST"]}',
            f'--port={db_settings["PORT"]}',
            f'--user={db_settings["USER"]}',
            f'--password={db_settings["PASSWORD"]}',
            '--single-transaction',
            '--routines',
            '--triggers',
            db_settings['NAME']
        ]

        with open(backup_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True)

        if compress:
            self.compress_file(backup_file)

    def backup_postgresql(self, db_settings, backup_file, compress):
        """Backup PostgreSQL database"""
        cmd = [
            'pg_dump',
            f'--host={db_settings["HOST"]}',
            f'--port={db_settings["PORT"]}',
            f'--username={db_settings["USER"]}',
            f'--dbname={db_settings["NAME"]}',
            '--no-password',
            '--verbose'
        ]

        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']

        with open(backup_file, 'w') as f:
            subprocess.run(cmd, stdout=f, env=env, check=True)

        if compress:
            self.compress_file(backup_file)

    def compress_file(self, file_path):
        """Compress a file with gzip"""
        compressed_path = f"{file_path}.gz"
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.writelines(f_in)

        # Remove original uncompressed file
        os.remove(file_path)
        
        # Update the file_path reference
        file_path = Path(compressed_path)
