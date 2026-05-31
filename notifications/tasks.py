import csv
import os
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from messaging.models import MessageLog
from .models import ExportJob

@shared_task
def export_logs_task(job_id):
    """
    Background export compiling user messages to CSV.
    """
    try:
        job = ExportJob.objects.get(pk=job_id)
    except ExportJob.DoesNotExist:
        return
        
    job.status = ExportJob.Status.PROCESSING
    job.save()
    
    try:
        user = job.user
        logs = MessageLog.objects.filter(user=user) if not user.is_admin else MessageLog.objects.all()
        
        # Create output directory
        exports_dir = os.path.join(settings.BASE_DIR, 'staticfiles', 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        filename = f"message_logs_{user.id}_{int(timezone.now().timestamp())}.csv"
        file_path = os.path.join(exports_dir, filename)
        
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Sender/Account', 'Direction', 'Recipient/Chat ID', 'Chat Title', 'Text', 'Status', 'Timestamp'])
            for log in logs:
                writer.writerow([
                    log.id,
                    log.telegram_account.phone_number,
                    log.direction,
                    log.chat_id,
                    log.chat_title or '',
                    log.message_text,
                    log.status,
                    log.sent_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
                
        # Update download link (for local dev, maps to staticfiles/exports/)
        job.download_url = f"/static/exports/{filename}"
        job.status = ExportJob.Status.COMPLETED
        job.save()
    except Exception as e:
        print(f"[Export Task Error] {e}")
        job.status = ExportJob.Status.FAILED
        job.save()
