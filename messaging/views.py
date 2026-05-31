import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import MessageLog

@login_required
@require_http_methods(["GET"])
def message_logs_list(request):
    """
    GET: List message logs with search, filter, and pagination parameters.
    """
    user = request.user
    
    # Base queryset based on role
    if user.is_admin:
        queryset = MessageLog.objects.all()
    else:
        queryset = MessageLog.objects.filter(user=user)
        
    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(message_text__icontains=q) |
            Q(chat_id__icontains=q) |
            Q(chat_title__icontains=q)
        )
        
    # Direction filter
    direction = request.GET.get('direction', '').strip()
    if direction in [MessageLog.Direction.INBOUND, MessageLog.Direction.OUTBOUND]:
        queryset = queryset.filter(direction=direction)
        
    # Telegram account filter
    account_id = request.GET.get('telegram_account_id', '').strip()
    if account_id:
        queryset = queryset.filter(telegram_account_id=account_id)
        
    # Pagination parameters
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
    except ValueError:
        page = 1
        page_size = 20
    
    page = max(1, page)
    page_size = max(1, min(100, page_size))  # Limit page size between 1-100
    
    total_count = queryset.count()
    total_pages = (total_count + page_size - 1) // page_size
    
    # Order and paginate
    queryset = queryset.select_related('telegram_account', 'user').order_by('-sent_at')[(page - 1) * page_size:page * page_size]
    
    data = [{
        'id': log.id,
        'user_email': log.user.email,
        'phone_number': log.telegram_account.phone_number,
        'telegram_account_id': log.telegram_account.id,
        'chat_id': log.chat_id,
        'chat_title': log.chat_title or log.chat_id,
        'message_text': log.message_text,
        'direction': log.direction,
        'status': log.status,
        'sent_at': log.sent_at.strftime('%Y-%m-%d %H:%M:%S')
    } for log in queryset]
    
    return JsonResponse({
        'success': True, 
        'logs': data,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total_count,
            'total_pages': total_pages
        }
    })
