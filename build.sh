#!/usr/bin/env bash
# exit on error
set -o errexit

# Bağımlılıkları yükle
pip install -r requirements.txt

# Statik dosyaları topla (CSS/JS)
python manage.py collectstatic --no-input

# Veritabanı tablolarını güncelle
python manage.py migrate