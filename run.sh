#!/bin/bash

# Bootstrap script for Django AI Messaging Dashboard

echo "🚀 Starting Django AI Messaging Dashboard bootstrap..."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found at venv/bin/activate"
    exit 1
fi

# Check if .env exists, if not copy from .env.example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📋 Creating .env from .env.example..."
        cp .env.example .env
        echo "⚠️  Please edit .env file with your actual API keys and secrets!"
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
else
    echo "📋 .env file already exists"
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Collect static files (optional but good practice)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start the development server
echo "🌐 Starting development server..."
echo "📝 Server will be available at: http://127.0.0.1:8000/dashboard/"
echo "🔐 Login credentials:"
echo "   Admin: admin@sdt.com / 123123123"
echo "   User: user@sdt.com / xcxcxcxc"
echo "   Viewer: view@sdt.com / sdt123456"
echo ""
echo "🛑 Press CTRL+C to stop the server"
echo ""

# Run the server
python manage.py runserver 0.0.0.0:8000