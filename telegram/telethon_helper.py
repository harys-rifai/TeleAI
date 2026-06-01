import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

def get_new_loop():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
    except Exception:
        return asyncio.get_event_loop()

async def async_send_code(api_id, api_hash, phone_number):
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    try:
        result = await client.send_code_request(phone_number)
        temp_session = client.session.save()
        return {
            'success': True,
            'phone_code_hash': result.phone_code_hash,
            'temp_session': temp_session
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await client.disconnect()

async def async_verify_code(api_id, api_hash, phone_number, code, phone_code_hash, temp_session):
    client = TelegramClient(StringSession(temp_session), api_id, api_hash)
    await client.connect()
    try:
        await client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
        final_session = client.session.save()
        # Fetch user info to verify
        me = await client.get_me()
        return {
            'success': True,
            'status': 'authenticated',
            'session_string': final_session,
            'username': me.username,
            'first_name': me.first_name
        }
    except SessionPasswordNeededError:
        # Save session string for the next 2FA step
        updated_session = client.session.save()
        return {
            'success': True,
            'status': 'needs_2fa',
            'temp_session': updated_session
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await client.disconnect()

async def async_verify_password(api_id, api_hash, password, temp_session):
    client = TelegramClient(StringSession(temp_session), api_id, api_hash)
    await client.connect()
    try:
        await client.check_password(password)
        final_session = client.session.save()
        me = await client.get_me()
        return {
            'success': True,
            'session_string': final_session,
            'username': me.username,
            'first_name': me.first_name
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await client.disconnect()

async def async_send_message(session_string, api_id, api_hash, target_chat, message_text):
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.connect()
    try:
        # Check if client is authorized
        if not await client.is_user_authorized():
            raise Exception("Client is not authorized. Session expired or revoked.")
        
        # Send message
        sent_msg = await client.send_message(target_chat, message_text)
        # Try to resolve chat title/info
        chat_entity = await client.get_input_entity(target_chat)
        chat_info = await client.get_entity(chat_entity)
        chat_title = getattr(chat_info, 'title', getattr(chat_info, 'first_name', str(target_chat)))
        
        return {
            'success': True,
            'msg_id': sent_msg.id,
            'chat_title': chat_title,
            'chat_id': str(sent_msg.peer_id.channel_id) if hasattr(sent_msg.peer_id, 'channel_id') else (
                str(sent_msg.peer_id.user_id) if hasattr(sent_msg.peer_id, 'user_id') else str(target_chat)
            )
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        await client.disconnect()

def send_code(api_id, api_hash, phone_number):
    loop = get_new_loop()
    return loop.run_until_complete(async_send_code(api_id, api_hash, phone_number))

def verify_code(api_id, api_hash, phone_number, code, phone_code_hash, temp_session):
    loop = get_new_loop()
    return loop.run_until_complete(async_verify_code(api_id, api_hash, phone_number, code, phone_code_hash, temp_session))

def verify_password(api_id, api_hash, password, temp_session):
    loop = get_new_loop()
    return loop.run_until_complete(async_verify_password(api_id, api_hash, password, temp_session))

def send_message(session_string, api_id, api_hash, target_chat, message_text):
    loop = get_new_loop()
    return loop.run_until_complete(async_send_message(session_string, api_id, api_hash, target_chat, message_text))
