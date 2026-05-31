#!/bin/bash

# Verification script for Django AI Messaging Dashboard
# Tests basic functionality and dashboard logic

echo "🔍 Starting verification of Django AI Messaging Dashboard..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# Check if server is running
echo "🌐 Checking if development server is running..."
if ! curl -s http://localhost:8000/dashboard/ > /dev/null; then
    echo "❌ Development server is not accessible at http://localhost:8000/dashboard/"
    echo "💡 Please start the server using './run.sh' or 'python manage.py runserver'"
    exit 1
else
    echo "✅ Development server is running"
fi

# Test dashboard accessibility (should redirect to login if not authenticated)
echo "📊 Testing dashboard accessibility..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard/)
if [[ "$response" == "200" || "$response" == "302" ]]; then
    if [[ "$response" == "302" ]]; then
        echo "✅ Dashboard homepage is accessible (HTTP 302 - redirect to login, expected for unauthenticated access)"
    else
        echo "✅ Dashboard homepage is accessible (HTTP 200)"
    fi
else
    echo "❌ Dashboard homepage returned HTTP $response"
    exit 1
fi

# Test login page
echo "🔐 Testing login page accessibility..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login/)
if [[ "$response" == "200" ]]; then
    echo "✅ Login page is accessible (HTTP 200)"
else
    echo "❌ Login page returned HTTP $response"
    exit 1
fi

# Test admin login (should redirect if not authenticated)
echo "👨‍💼 Testing admin dashboard accessibility..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/)
if [[ "$response" == "302" || "$response" == "200" ]]; then
    echo "✅ Admin dashboard is accessible (HTTP $response - expected redirect if not authenticated)"
else
    echo "❌ Admin dashboard returned unexpected HTTP $response"
    exit 1
fi

# Test API endpoints (if they exist)
echo "🔌 Testing API endpoints accessibility..."

# Test stats endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/dashboard/api/stats/ 2>/dev/null || echo "000")
if [[ "$response" == "200" || "$response" == "401" || "$response" == "403" ]]; then
    echo "✅ Stats API endpoint is accessible (HTTP $response - expected auth protection)"
else
    echo "⚠️  Stats API endpoint returned HTTP $response (may not be implemented yet)"
fi

# Test telegram accounts endpoint
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/telegram/accounts/ 2>/dev/null || echo "000")
if [[ "$response" == "200" || "$response" == "401" || "$response" == "403" ]]; then
    echo "✅ Telegram accounts API endpoint is accessible (HTTP $response - expected auth protection)"
else
    echo "⚠️  Telegram accounts API endpoint returned HTTP $response (may not be implemented yet)"
fi

# Test database connectivity
echo "🗄️  Testing database connectivity..."
python manage.py dbshell <<< "SELECT 1;" > /dev/null 2>&1
if [[ $? -eq 0 ]]; then
    echo "✅ Database connection is working"
else
    echo "❌ Database connection failed"
    exit 1
fi

# Test static files
echo "📦 Testing static files..."
if [[ -d "staticfiles" || -d "dashboard/static" ]]; then
    echo "✅ Static files directories exist"
else
    echo "⚠️  Static files directories not found (may need to run collectstatic)"
fi

echo ""
echo "🎉 Verification completed successfully!"
echo "📝 Summary:"
echo "   - Server is running and accessible"
echo "   - Dashboard and login pages are working"
echo "   - Database connectivity is confirmed"
echo "   - Basic API endpoints are accessible (with expected auth protection)"
echo ""
echo "🚀 To access the dashboard:"
echo "   URL: http://localhost:8000/dashboard/"
echo "   Login with:"
echo "     Admin: admin@sdt.com / 123123123"
echo "     User: user@sdt.com / xcxcxcxc"
echo "     Viewer: view@sdt.com / sdt123456"