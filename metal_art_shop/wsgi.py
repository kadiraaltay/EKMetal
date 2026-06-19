import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise  # KANKA: Whitenoise'u buraya çağırıyoruz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metal_art_shop.settings')

application = get_wsgi_application()

# KANKA: Django ayağa kalkarken statik dosyaları bu satır sayesinde dünyaya aslanlar gibi servis edecek!
application = WhiteNoise(application, root=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles'))