"""
WSGI config for realnaijagist project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realnaijagist.settings')

application = get_wsgi_application()

# DEPLOY_RESTART_TRIGGER: 2026-03-04T12:10
# Namecheap deploy hook: Wed Mar  4 03:13:37 PM WAT 2026
# Namecheap deploy hook: Wed Mar  4 03:49:38 PM WAT 2026
# Namecheap deploy hook: Wed Mar  4 03:56:32 PM WAT 2026
# Namecheap deploy hook: Wed Mar  4 04:34:20 PM WAT 2026
# Namecheap deploy hook: Wed Mar  4 04:39:45 PM WAT 2026
