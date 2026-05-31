from django.db import migrations
from django.contrib.auth.hashers import make_password

def seed_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    # Create Admin
    admin_user = User(
        email='admin@sdt.com',
        username='admin@sdt.com',  # Username is required and unique
        role='admin',
        is_staff=True,
        is_superuser=True,
        is_active=True,
        password=make_password('123123123')
    )
    admin_user.save()
    
    # Create Regular User
    regular_user = User(
        email='user@sdt.com',
        username='user@sdt.com',
        role='user',
        is_active=True,
        password=make_password('xcxcxcxc')
    )
    regular_user.save()
    
    # Create Viewer
    viewer_user = User(
        email='view@sdt.com',
        username='view@sdt.com',
        role='viewer',
        is_active=True,
        password=make_password('sdt123456')
    )
    viewer_user.save()

def rollback_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(email__in=['admin@sdt.com', 'user@sdt.com', 'view@sdt.com']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_users, rollback_users),
    ]
