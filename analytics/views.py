from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDay
from datetime import timedelta
from messaging.models import MessageLog
from .clickhouse_client import get_clickhouse_metrics

@login_required
@require_http_methods(["GET"])
def analytics_metrics(request):
    """
    GET: Return message analytics metrics. Fallback to PostgreSQL if ClickHouse is offline.
    """
    user = request.user
    days = int(request.GET.get('days', 7))
    
    # Try ClickHouse first (only for non-viewers or based on request, but standard fallback)
    metrics = None
    try:
        metrics = get_clickhouse_metrics(user.id, days)
    except Exception:
        metrics = None
        
    if metrics is not None:
        metrics['source'] = 'clickhouse'
        return JsonResponse({'success': True, 'data': metrics})
        
    # FALLBACK: Aggregations using PostgreSQL MessageLog
    start_date = timezone.now() - timedelta(days=days)
    
    if user.is_admin:
        logs = MessageLog.objects.filter(sent_at__gte=start_date)
    else:
        logs = MessageLog.objects.filter(user=user, sent_at__gte=start_date)
        
    # Daily aggregation
    daily_stats = logs.annotate(day=TruncDay('sent_at')) \
                      .values('day') \
                      .annotate(
                          msg_count=Count('id'),
                          outbound_count=Count('id', filter=Q(direction=MessageLog.Direction.OUTBOUND)),
                          inbound_count=Count('id', filter=Q(direction=MessageLog.Direction.INBOUND)),
                          success_count=Count('id', filter=Q(status=MessageLog.Status.SUCCESS)),
                          failed_count=Count('id', filter=Q(status=MessageLog.Status.FAILED))
                      ).order_by('day')
                      
    daily_list = []
    for item in daily_stats:
        # Construct word count estimation for logs (fallback to length-based word count)
        # Note: In Django database queries, counting words can be simulated,
        # but to keep it simple, we retrieve the records of that day or average it
        day_logs = logs.filter(sent_at__date=item['day'].date())
        total_words = sum(len(log.message_text.split()) for log in day_logs)
        
        daily_list.append({
            'day': item['day'].strftime('%Y-%m-%d'),
            'msg_count': item['msg_count'],
            'total_words': total_words,
            'outbound_count': item['outbound_count'],
            'inbound_count': item['inbound_count'],
            'success_count': item['success_count'],
            'failed_count': item['failed_count']
        })
        
    # Overall summary stats
    total_count = logs.count()
    success_count = logs.filter(status=MessageLog.Status.SUCCESS).count()
    failed_count = logs.filter(status=MessageLog.Status.FAILED).count()
    
    total_words_overall = sum(len(log.message_text.split()) for log in logs)
    avg_words = round(total_words_overall / total_count, 1) if total_count > 0 else 0
    success_rate = round((success_count / total_count * 100) if total_count > 0 else 100, 1)
    
    fallback_metrics = {
        'daily': daily_list,
        'summary': {
            'total': total_count,
            'avg_words_per_msg': avg_words,
            'success_rate': success_rate,
            'success': success_count,
            'failed': failed_count
        },
        'source': 'postgresql'
    }
    
    return JsonResponse({'success': True, 'data': fallback_metrics})
