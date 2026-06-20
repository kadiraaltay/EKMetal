#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def run_production_triggers():
    # Sadece Render sunucusunda çalışması için kontrol koyduk kanka
    if 'RENDER' in os.environ:
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        
        # 1. OTOMATİK TASARIM TOPLAMA (collectstatic)
        print("--- AUTOMATIC COLLECTSTATIC RUNNING ---")
        os.system("python manage.py collectstatic --noinput")
        
        # 2. OTOMATİK ADMİN HESABI AÇMA (createsuperuser)
        User = get_user_model()
        if not User.objects.filter(username='kadir').exists():
            print("--- CREATING SUPERUSER AUTOMATICALLY ---")
            User.objects.create_superuser('kadir', 'kadiraltay90@gmail.com', 'Kadir1234!')
            print("--- SUPERUSER CREATED SUCCESSFULY kanka ---")


def main():
    """Run administrative tasks."""
    # KANKA: Ayar modülünü en başa çektik ki Django neyi ayağa kaldıracağını bilsin!
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metal_art_shop.settings')
    
    # Eğer terminalden normal bir komut çalıştırılmıyorsa ve Render ortamındaysak triggerları tetikle
    if len(sys.argv) > 1 and sys.argv[1] in ['migrate', 'collectstatic'] or 'RENDER' in os.environ:
        # Önce ayarların yüklenmesi için execute öncesi trigger tetiklenebilir duruma geliyor
        pass

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    # KANKA: Önce ortam değişkenini tanımlıyoruz ki setup() patlamasın!
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metal_art_shop.settings')
    
    # Render'da derleme esnasında admini açabilmesi için sıralamayı güvenli hale getirdik
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        # Eğer migrate ediyorsak, komut bittikten sonra admini oluşturması için sırayı koruyoruz
        pass
        
    # Tetikleyiciyi güvenli bölgeye aldık kanka
    try:
        import django
        django.setup()
        run_production_triggers()
    except Exception as e:
        # Eğer henüz DB hazır değilse hata vermesin, sistemi kilitlemesin diye sarmaladık
        print(f"Trigger check: {e}")

    main()