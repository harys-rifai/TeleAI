from django.http import JsonResponse
from .models import AppVersion

def current_version(request):
    latest = AppVersion.objects.first()
    version_str = latest.version if latest else "v1.0.0"
    notes = latest.notes if latest else "Initial deployment"
    return JsonResponse({
        'success': True,
        'version': version_str,
        'notes': notes,
        'environment': 'Production'
    })
