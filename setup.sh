#!/bin/bash

# Stop script if error
set -e

echo "🚀 Starting Django project setup..."

# Detect Python command (On Windows Git Bash, usually 'python')
if command -v python &> /dev/null; then
    PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Python not found! Please install Python."
    exit 1
fi

# 1. Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# 2. Activate virtual environment
echo "🔄 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# 3. Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# 4. Install dependencies
if [ -f requirements.txt ]; then
    echo "📥 Installing dependencies from requirements.txt..."
    python -m pip install -r requirements.txt --no-cache-dir
else
    echo "⚠️ requirements.txt not found, installing Django..."
    python -m pip install django
fi

# 5. Setup .env if exists
if [ -f .env.example ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# 6. Run migrations
echo "🛠 Ensuring all model changes are captured and running migrations..."
python manage.py makemigrations --noinput || { echo "❌ Makemigrations failed"; exit 1; }
python manage.py migrate --noinput || { echo "❌ Migrate failed"; exit 1; }

# 7. Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# 8. Create superuser (optional skip)
echo "👤 Creating superuser (optional, skip with Ctrl+C)..."
python manage.py createsuperuser || true

echo ""
echo "✅ Setup completed successfully!"
echo "🚀 You can now start the dashboard by running:"
echo "   bash run.sh"
echo ""
echo "💡 Remember to start Celery in another terminal for background tasks."