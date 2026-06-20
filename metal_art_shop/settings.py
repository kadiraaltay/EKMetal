import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-!i$f_x-b-n#=(&1wacz+d9w$-1&kf2cbx8ou4b*o@4amg&+l6h'

# KANKA: Lokalde rahatça çalışabilmemiz ve hata ayıklayabilmemiz için TRUE moduna geri çektik!
DEBUG = True

# Lokalde sorunsuz çalışması için gerekli hostlar
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',  # Senin canavar uygulaman kanka
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # KANKA: Render'da CSS ve JS'ler patlamasın diye tam buraya mühürledik!
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'metal_art_shop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.cart_item_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'metal_art_shop.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# STATİK VE MEDYA DOSYA AYARLARI (RENDER VE WHITENOISE UYUMLU DURUMA GETİRİLDİ KANKA)
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Eğer projenin ana dizininde elle oluşturduğun bir static klasörü varsa Django görsün diye:
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# KANKA: Render canlı ortamında statik dosyaları sıkıştırıp cache'lemesi için WhiteNoise motorunu bağlıyoruz
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ==============================================================================
# GÜVENLİK VE YÖNLENDİRME AYARLARI
# ==============================================================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'


# ==============================================================================
# KURUMSAL OTOMATİK E-POSTA VE FATURA AYARLARI
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'kadiraltay90@gmail.com'
EMAIL_HOST_PASSWORD = 'qsem njqn vsoj rbfa'
DEFAULT_FROM_EMAIL = f"EK Metal Wall Art <{EMAIL_HOST_USER}>"


# ==============================================================================
# IYZICO PAYMENT GATEWAY SETTINGS (SANDBOX/TEST MODU)
# ==============================================================================
IYZICO_API_KEY = 'sandbox-txt-AokvB32gYfhU7K8L9M1N2O3P4'
IYZICO_SECRET_KEY = 'sandbox-txt-ZxpQ98rStUvW65xY43zQ21w'
IYZICO_BASE_URL = 'https://api.api.iyzico.com'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'