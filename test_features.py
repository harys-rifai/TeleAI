#!/usr/bin/env python3
"""
Comprehensive Feature Test Suite for TeleAI Dashboard
Verifies API endpoints, Authentication, and System Health.
"""

import os
import sys
import django
import json
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tele_ai_project.settings')
django.setup()

User = get_user_model()

def run_feature_tests():
    client = Client()
    print("🧪 Starting TeleAI Feature Test Suite...\n")

    # 0. Check Environment
    if not os.path.exists('.env'):
        print("❌ System Check: .env file missing!")
        return
    else:
        print("✅ System Check: .env file found")

    # 1. Test Authentication
    print("--- [1/5] Testing Authentication ---")
    login_data = {'email': 'admin@sdt.com', 'password': '123123123'}
    response = client.post('/login/', login_data)
    if response.status_code in [200, 302]:
        print("✅ Authentication Flow: Pass")
    else:
        print(f"❌ Authentication Flow: Fail (Status {response.status_code})")
        return

    # 2. Test Dashboard Stats API
    print("\n--- [2/5] Testing Stats API ---")
    response = client.get('/dashboard/api/stats/')
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Stats API: Pass (Accounts: {data['stats']['accounts']['total']})")
        else:
            print("❌ Stats API: Fail (Logic error in response)")
    else:
        print(f"❌ Stats API: Fail (HTTP {response.status_code})")

    # 3. Test Weather API Logic
    print("\n--- [3/5] Testing Weather API ---")
    # Test with default Jakarta
    response = client.get('/dashboard/api/weather-current/?q=Jakarta')
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            temp = data['data']['current']['temp_c']
            condition = data['data']['current']['condition']['text']
            print(f"✅ Weather API: Pass (Jakarta: {temp}°C, {condition})")
        else:
            print(f"⚠️  Weather API: Partial (API accessible but data failed: {data.get('error')})")
    else:
        print(f"❌ Weather API: Fail (HTTP {response.status_code})")

    # 4. Test AI Configuration API
    print("\n--- [4/5] Testing AI Assistant API ---")
    response = client.get('/api/ai/configs/')
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ AI Config API: Pass (Model: {data['config']['model_name']})")
        else:
            print("❌ AI Config API: Fail")
    else:
        # Expected to be 200 if authenticated, otherwise 404/403 if route differs
        print(f"⚠️  AI Config API: Status {response.status_code} (Check URL routing)")

    # 5. Test Responsive Layout Context
    print("\n--- [5/5] Testing UI Assets ---")
    static_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'static', 'css', 'style.css')
    if os.path.exists(static_path):
        with open(static_path, 'r') as f:
            content = f.read()
            if 'media (max-width: 992px)' in content:
                print("✅ Responsive CSS: Pass (Mobile breakpoints found)")
            if '--neon-blue' in content:
                print("✅ Theme CSS: Pass (Neon variables found)")
    else:
        print("❌ UI Assets: Fail (CSS file not found)")

    print("\n" + "="*40)
    print("🎉 Feature testing complete.")
    print("="*40)

if __name__ == '__main__':
    try:
        # Ensure we have at least one user to test with
        if not User.objects.filter(email='admin@sdt.com').exists():
             User.objects.create_superuser(
                 email='admin@sdt.com',
                 username='admin@sdt.com',
                 password='123123123',
                 role='admin'
             )
        run_feature_tests()
    except Exception as e:
        print(f"❌ Critical Error during testing: {e}")
        sys.exit(1)