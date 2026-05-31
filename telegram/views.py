import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.decorators import method_decorator
from .models import TelegramAccount
from . import telethon_helper

@login_required
@require_http_methods(["GET", "POST"])
def telegram_accounts_list(request):
    """
    GET: List all telegram accounts based on role with pagination.
    POST: Create a basic entry (for manual/bot accounts) or check fields.
    """
    user = request.user
    
    if request.method == "GET":
        if user.is_admin:
            queryset = TelegramAccount.objects.all()
        else:
            queryset = TelegramAccount.objects.filter(user=user)
        
        # Pagination parameters
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
        except ValueError:
            page = 1
            page_size = 10
        
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        
        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size
        
        accounts = queryset[(page - 1) * page_size:page * page_size]
            
        data = [{
            'id': acc.id,
            'user_email': acc.user.email,
            'phone_number': acc.phone_number,
            'api_id': acc.api_id,
            'api_hash': acc.api_hash[:6] + "..." if acc.api_hash else "",
            'is_active': acc.is_active,
            'has_session': bool(acc.session_string),
            'created_at': acc.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for acc in accounts]
        return JsonResponse({
            'success': True, 
            'accounts': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': total_pages
            }
        })
        
    elif request.method == "POST":
        if user.is_viewer:
            return JsonResponse({'success': False, 'error': 'Viewer role cannot register accounts.'}, status=403)
            
        try:
            body = json.loads(request.body)
            phone_number = body.get('phone_number')
            api_id = int(body.get('api_id'))
            api_hash = body.get('api_hash')
            bot_token = body.get('bot_token', '')
            
            # Simple validation
            if not phone_number or not api_id or not api_hash:
                return JsonResponse({'success': False, 'error': 'api_id, api_hash, and phone_number are required.'})
                
            # Create or update inactive placeholder
            account, created = TelegramAccount.objects.update_or_create(
                user=user,
                phone_number=phone_number,
                defaults={
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'bot_token': bot_token,
                    'is_active': False
                }
            )
            return JsonResponse({'success': True, 'message': 'Account registered. Please proceed to authenticate.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_telegram_account(request, pk):
    """
    Delete a Telegram account configuration.
    """
    user = request.user
    if user.is_viewer:
        return JsonResponse({'success': False, 'error': 'Viewer role cannot delete accounts.'}, status=403)
        
    if user.is_admin:
        account = get_object_or_404(TelegramAccount, pk=pk)
    else:
        account = get_object_or_404(TelegramAccount, pk=pk, user=user)
        
    account.delete()
    return JsonResponse({'success': True, 'message': 'Telegram account deleted successfully.'})

@login_required
@require_http_methods(["POST"])
def send_auth_code(request):
    """
    Initiate Telethon auth: send code to phone.
    """
    user = request.user
    if user.is_viewer:
        return JsonResponse({'success': False, 'error': 'Viewer role cannot authenticate.'}, status=403)
        
    try:
        body = json.loads(request.body)
        phone = body.get('phone_number')
        api_id = int(body.get('api_id'))
        api_hash = body.get('api_hash')
        
        if not phone or not api_id or not api_hash:
            return JsonResponse({'success': False, 'error': 'api_id, api_hash, and phone_number are required.'})
            
        res = telethon_helper.send_code(api_id, api_hash, phone)
        if res.get('success'):
            # Store in session
            request.session['auth_phone'] = phone
            request.session['auth_api_id'] = api_id
            request.session['auth_api_hash'] = api_hash
            request.session['auth_phone_code_hash'] = res['phone_code_hash']
            request.session['auth_temp_session'] = res['temp_session']
            return JsonResponse({'success': True, 'message': 'Verification code sent.'})
        else:
            return JsonResponse({'success': False, 'error': res.get('error')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def verify_auth_code(request):
    """
    Verify code sent to phone.
    """
    user = request.user
    if user.is_viewer:
        return JsonResponse({'success': False, 'error': 'Viewer role cannot authenticate.'}, status=403)
        
    try:
        body = json.loads(request.body)
        code = body.get('code')
        
        phone = request.session.get('auth_phone')
        api_id = request.session.get('auth_api_id')
        api_hash = request.session.get('auth_api_hash')
        phone_code_hash = request.session.get('auth_phone_code_hash')
        temp_session = request.session.get('auth_temp_session')
        
        if not code or not phone or not api_id or not api_hash or not phone_code_hash or not temp_session:
            return JsonResponse({'success': False, 'error': 'Invalid request or session expired. Restart authentication.'})
            
        res = telethon_helper.verify_code(api_id, api_hash, phone, code, phone_code_hash, temp_session)
        if res.get('success'):
            if res.get('status') == 'needs_2fa':
                # Update session string in django session
                request.session['auth_temp_session'] = res['temp_session']
                return JsonResponse({'success': True, 'status': 'needs_2fa', 'message': '2FA Password Required.'})
                
            # Authentication successful
            session_string = res.get('session_string')
            
            # Save or update TelegramAccount
            account, created = TelegramAccount.objects.update_or_create(
                user=user,
                phone_number=phone,
                defaults={
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'session_string': session_string,
                    'is_active': True
                }
            )
            
            # Clear session
            clean_auth_session(request)
            return JsonResponse({'success': True, 'status': 'authenticated', 'message': 'Authenticated successfully.'})
        else:
            return JsonResponse({'success': False, 'error': res.get('error')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def verify_2fa_password(request):
    """
    Verify 2FA password.
    """
    user = request.user
    if user.is_viewer:
        return JsonResponse({'success': False, 'error': 'Viewer role cannot authenticate.'}, status=403)
        
    try:
        body = json.loads(request.body)
        password = body.get('password')
        
        phone = request.session.get('auth_phone')
        api_id = request.session.get('auth_api_id')
        api_hash = request.session.get('auth_api_hash')
        temp_session = request.session.get('auth_temp_session')
        
        if not password or not phone or not api_id or not api_hash or not temp_session:
            return JsonResponse({'success': False, 'error': 'Session expired or missing fields.'})
            
        res = telethon_helper.verify_password(api_id, api_hash, password, temp_session)
        if res.get('success'):
            session_string = res.get('session_string')
            
            account, created = TelegramAccount.objects.update_or_create(
                user=user,
                phone_number=phone,
                defaults={
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'session_string': session_string,
                    'is_active': True
                }
            )
            clean_auth_session(request)
            return JsonResponse({'success': True, 'message': 'Authenticated successfully with 2FA.'})
        else:
            return JsonResponse({'success': False, 'error': res.get('error')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def clean_auth_session(request):
    for key in ['auth_phone', 'auth_api_id', 'auth_api_hash', 'auth_phone_code_hash', 'auth_temp_session']:
        if key in request.session:
            del request.session[key]
