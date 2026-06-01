#!/usr/bin/env python3
"""
Simple test script to verify login functionality and dashboard access
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tele_ai_project.settings')
sys.path.append('/Users/harysrifai/web/teleAI')

# Initialize Django
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def test_login_credentials():
    """Test that we can authenticate with the default credentials"""
    print("🔐 Testing login credentials...")
    
    # Test admin credentials
    user = authenticate(username='admin@sdt.com', password='123123123')
    if user is not None:
        print("✅ Admin credentials are valid")
    else:
        print("❌ Admin credentials are invalid")
        return False
    
    # Test user credentials
    user = authenticate(username='user@sdt.com', password='xcxcxcxc')
    if user is not None:
        print("✅ User credentials are valid")
    else:
        print("❌ User credentials are invalid")
        return False
        
    # Test viewer credentials
    user = authenticate(username='view@sdt.com', password='sdt123456')
    if user is not None:
        print("✅ Viewer credentials are valid")
    else:
        print("❌ Viewer credentials are invalid")
        return False
    
    return True

def test_dashboard_access_with_client():
    """Test dashboard access using Django test client"""
    print("\n🌐 Testing dashboard access with Django test client...")
    
    client = Client()
    
    # Test login page
    response = client.get('/login/')
    if response.status_code == 200:
        print("✅ Login page is accessible")
    else:
        print(f"❌ Login page returned status {response.status_code}")
        return False
    
    # Test dashboard access without login (should redirect)
    response = client.get('/dashboard/')
    if response.status_code == 302:
        print("✅ Dashboard correctly redirects unauthenticated users to login")
    else:
        print(f"❌ Dashboard returned unexpected status {response.status_code}")
        return False
    
    # Test login with admin credentials
    login_success = client.login(username='admin@sdt.com', password='123123123')
    if login_success:
        print("✅ Admin login successful via test client")
    else:
        print("❌ Admin login failed via test client")
        return False
    
    # Test dashboard access after login
    response = client.get('/dashboard/')
    if response.status_code == 200:
        print("✅ Dashboard accessible after login")
    else:
        print(f"❌ Dashboard returned status {response.status_code} after login")
        return False
    
    # Test logout
    response = client.get('/logout/')
    if response.status_code == 302:
        print("✅ Logout successful")
    else:
        print(f"❌ Logout returned status {response.status_code}")
        return False
    
    return True

def main():
    print("🧪 Running Django AI Messaging Dashboard login tests...\n")
    
    success = True
    
    # Test 1: Direct authentication
    success &= test_login_credentials()
    
    # Test 2: Django test client
    success &= test_dashboard_access_with_client()
    
    print("\n" + "="*50)
    if success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())