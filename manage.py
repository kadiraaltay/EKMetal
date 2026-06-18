#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metal_art_shop.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)




#render ekranı için silinebilir sonradan
def run_production_triggers():
    # Sadece Render sunucusunda çalışması için kontrol koyduk kanka
    if 'RENDER' in os.environ:
        from django.contrib.auth import get_user_model
        import django
        django.setup()
        
        # 1. OTOMATİK TASARIM TOPLAMA (collectstatic)
        print("--- AUTOMATIC COLLECTSTATIC RUNNING ---")
        os.system("python manage.py collectstatic --noinput")
        
        # 2. OTOMATİK ADMİN HESABI AÇMA (createsuperuser)
        User = get_user_model()
        if not User.objects.filter(username='kadir').exists():
            print("--- CREATING SUPERUSER AUTOMATICALLY ---")
            User.objects.create_superuser('kadir', 'kadiraltay90@gmail.com', 'Kadir1234!')
            print("--- SUPERUSER CREATED SUCCESSFULY kanka ---")


if __name__ == '__main__':
    run_production_triggers()
    main()
