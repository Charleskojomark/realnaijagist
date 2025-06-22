from .models import Category
from django.conf import settings

def global_context(request):
    return {
        'categories': Category.objects.all(),
        'current_year': settings.CURRENT_YEAR,
    }