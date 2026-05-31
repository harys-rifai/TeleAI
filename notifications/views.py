import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import ExportJob
from .tasks import export_logs_task

@login_required
@require_http_methods(["GET", "POST"])
def export_jobs_api(request):
    user = request.user
    
    if request.method == "GET":
        jobs = ExportJob.objects.filter(user=user)[:20]
        data = [{
            'id': job.id,
            'export_type': job.export_type,
            'status': job.status,
            'download_url': job.download_url,
            'created_at': job.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for job in jobs]
        return JsonResponse({'success': True, 'jobs': data})
        
    elif request.method == "POST":
        if user.is_viewer:
            return JsonResponse({'success': False, 'error': 'Viewer role cannot trigger log exports.'}, status=403)
            
        try:
            # Create pending job
            job = ExportJob.objects.create(
                user=user,
                export_type='CSV',
                status=ExportJob.Status.PENDING
            )
            
            # Run Celery task asynchronously
            export_logs_task.delay(job.id)
            
            return JsonResponse({
                'success': True,
                'message': 'Log export job started in the background.',
                'job_id': job.id
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
