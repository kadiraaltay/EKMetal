import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-!i$f_x-b-n#=(&1wacz+d9w$-1&kf2cbx8ou4b*o@4amg&+l6h'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# metal_art_shop/settings.py dosyasının en altına ekle kanka:

STRIPE_PUBLIC_KEY = "pk_test_51TjMiNRzYUZyjidIIQO2Bn0FwN0qpEejVh3eRe09shERriYk3DQxB1TWxyzs3HBfmZ3RcK0GpoN0fczSM5a1nVr200i9BRAsBr"
STRIPE_SECRET_KEY = "sk_test_51TjMiNRzYUZyjidIyvYsmqJutyjX42XKSpGtAQPSSJni9YqZmO41Rduq42Xo57ieLo8FkWy6lq3IbZ7BQnBN6Xhu00r03T6LFi"

LOGIN_URL = '/login/'  # Kullanıcı giriş yapmadıysa bizim 'login' isimli url'imize gitsin
LOGIN_REDIRECT_URL = '/'  # Giriş yaptıktan sonra direkt ana sayfaya (veya sepetine) dönsün

# metal_art_shop/settings.py en altına ekle kanka:

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'kadiraltay90@gmail.com' # Buraya kurumsal ya da kendi Gmail'ini yaz kanka
EMAIL_HOST_PASSWORD = 'qsem njqn vsoj rbfa' # Gmail'den alacağın "Uygulama Şifresi" (App Password) gelecek buraya
DEFAULT_FROM_EMAIL = f"EK Metal Wall Art <{EMAIL_HOST_USER}>"