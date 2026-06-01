#!/bin/bash

# Bootstrap script for Django AI Messaging Dashboard

echo "🚀 Starting Django AI Messaging Dashboard bootstrap..."

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    echo "📦 Activating virtual environment (Windows)..."
    source venv/Scripts/activate
else
    echo "❌ Virtual environment not found."
    echo "💡 Please run 'bash setup.sh' first to install dependencies and initialize the project."
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
python manage.py makemigrations --noinput || { echo "❌ Makemigrations failed"; exit 1; }
python manage.py migrate --noinput || { echo "❌ Migration failed"; exit 1; }

# Collect static files (optional but good practice)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || echo "⚠️  Static collection failed, skipping..."

# Check Redis status (required for Celery/Scheduler)
if ! command -v redis-cli &> /dev/null || ! redis-cli ping &> /dev/null; then
    echo "⚠️  Warning: Redis is not running or redis-cli not found."
    echo "   Celery tasks for scheduled messages and weather will not work!"
fi

# Check for required environment variables
if ! python -c "import os; from dotenv import load_dotenv; load_dotenv(); exit(0 if os.getenv('SECRET_KEY') else 1)"; then
    echo "❌ Error: SECRET_KEY not found in .env"
    exit 1
fi

# Check ClickHouse status
if ! curl -s http://localhost:8123/ping &> /dev/null; then
    echo "⚠️  Warning: ClickHouse is not responding on port 8123 (HTTP)."
    echo "   Analytics and metrics metrics will not be available!"
fi

# Start the development server
echo "🌐 Starting development server..."
echo "📝 Server will be available at: http://127.0.0.1:8000/dashboard/"
echo "⚙️  Background Tasks: To enable scheduling, run this in another terminal:"
echo "   source venv/Scripts/activate"
echo "   celery -A tele_ai_project worker --beat -l info"
echo ""
echo "🔐 Login credentials:"
echo "   Admin: admin@sdt.com / 123123123"
echo "   User: user@sdt.com / xcxcxcxc"
echo "   Viewer: view@sdt.com / sdt123456"
echo ""
echo "🛑 Press CTRL+C to stop the server"
echo ""

# Run the server
python manage.py runserver 0.0.0.0:8000