#!/bin/bash

# Stop script if error
set -e

echo "🚀 Starting Django project setup..."

# 1. Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# 2. Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# 4. Install dependencies
if [ -f requirements.txt ]; then
    echo "📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found, installing Django..."
    pip install django
fi

# 5. Setup .env if exists
if [ -f .env.example ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# 6. Run migrations
echo "🛠 Running migrations..."
python manage.py migrate

# 7. Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# 8. Create superuser (optional skip)
echo "👤 Creating superuser (optional, skip with Ctrl+C)..."
python manage.py createsuperuser || true

# 9. Run server
echo "🌐 Starting development server..."
python manage.py runserver

echo "✅ Django is running!"