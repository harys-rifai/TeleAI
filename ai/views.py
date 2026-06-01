import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import AIConfig
from .services import generate_ai_reply

@login_required
@require_http_methods(["GET", "POST"])
def ai_config_api(request):
    """
    GET: Get current user AI Configuration parameters.
    POST: Update user AI Configuration parameters.
    """
    user = request.user
    
    # Auto-get or create config
    config, created = AIConfig.objects.get_or_create(
        user=user,
        defaults={
            'system_prompt': 'You are a helpful assistant responding to Telegram inquiries.',
            'model_name': 'gpt-4o',
            'temperature': 0.7,
            'is_auto_reply_enabled': False
        }
    )
    
    if request.method == "GET":
        return JsonResponse({
            'success': True,
            'config': {
                'id': config.id,
                'model_name': config.model_name,
                'system_prompt': config.system_prompt,
                'temperature': config.temperature,
                'is_auto_reply_enabled': config.is_auto_reply_enabled,
                'has_custom_key': bool(config.api_key),
                'api_base_url': config.api_base_url or ''
            }
        })
        
    elif request.method == "POST":
        if user.is_viewer:
            return JsonResponse({'success': False, 'error': 'Viewer role cannot modify AI settings.'}, status=403)
            
        try:
            body = json.loads(request.body)
            config.model_name = body.get('model_name', config.model_name).strip()
            config.system_prompt = body.get('system_prompt', config.system_prompt).strip()
            config.temperature = float(body.get('temperature', config.temperature))
            config.is_auto_reply_enabled = bool(body.get('is_auto_reply_enabled', config.is_auto_reply_enabled))
            config.api_base_url = body.get('api_base_url', config.api_base_url).strip() or None
            
            # API Key can be submitted as blank or asterisks if unchanged
            new_key = body.get('api_key', '').strip()
            if new_key and not new_key.startswith('***'):
                config.api_key = new_key
            elif new_key == '':
                # If explicitly cleared
                config.api_key = None
                
            config.save()
            return JsonResponse({'success': True, 'message': 'AI Configuration updated.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def ai_test_prompt(request):
    """
    POST: Test a user message prompt against OpenAI and return the generated answer.
    """
    user = request.user
    try:
        body = json.loads(request.body)
        prompt = body.get('prompt', '').strip()
        
        if not prompt:
            return JsonResponse({'success': False, 'error': 'Prompt text is required.'})
            
        reply = generate_ai_reply(user, prompt)
        return JsonResponse({'success': True, 'reply': reply})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
