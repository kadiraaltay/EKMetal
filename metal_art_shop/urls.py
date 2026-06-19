from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Yönetim Paneli
    path('admin/', admin.site.urls),
    
    # shop uygulamasının tertemiz urls.py bağlantısı
    path('', include('shop.urls')),
]

# Kanka: DEBUG = True modunda hem görsellerin (media) hem de CSS/JS (static) dosyalarının 
# yerel sunucuda kusursuz yüklenmesini bu kurumsal satırlarla güvenceye alıyoruz.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)