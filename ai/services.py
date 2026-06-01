from openai import OpenAI
from django.conf import settings
from .models import AIConfig

def get_openai_client(user):
    """
    Get OpenAI Client using user specific api key, or fallback to global settings.
    """
    api_key = None
    api_base_url = None
    try:
        config = user.ai_config
        api_key = config.api_key or settings.OPENAI_API_KEY
        api_base_url = config.api_base_url
    except AIConfig.DoesNotExist:
        api_key = settings.OPENAI_API_KEY
        
    if not api_key:
        return None
        
    client_kwargs = {"api_key": api_key}
    if api_base_url:
        client_kwargs["base_url"] = api_base_url
    
    return OpenAI(**client_kwargs)

def generate_ai_reply(user, prompt, chat_history=None):
    """
    Generate reply using OpenAI Chat Completion API.
    """
    client = get_openai_client(user)
    if not client:
        return "Error: OpenAI API Key is not configured."
        
    try:
        # Load user configuration parameters
        model_name = "gpt-4o"
        system_prompt = "You are a helpful assistant."
        temperature = 0.7
        
        try:
            config = user.ai_config
            model_name = config.model_name
            system_prompt = config.system_prompt
            temperature = config.temperature
        except AIConfig.DoesNotExist:
            pass
            
        messages = [{"role": "system", "content": system_prompt}]
        
        # Optionally append history
        if chat_history:
            for speaker, text in chat_history:
                role = "assistant" if speaker == "ai" or speaker == "bot" else "user"
                messages.append({"role": role, "content": text})
                
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[AI Error] Failed to generate response: {str(e)}"
