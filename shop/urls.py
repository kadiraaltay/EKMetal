from django.urls import path
from . import views

urlpatterns = [
    # Ana Sayfa ve Ürün Detay
    path('', views.index, name='index'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Sepet Yönetim İşlemleri
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Kupon Sistemi
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),

    # Kullanıcı Yetkilendirme ve Profil
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Ödeme ve Sipariş Tamamlama (iyzico)
    path('checkout/', views.checkout_view, name='checkout'),
    path('payment-success/', views.payment_success_view, name='payment_success'),
    path('payment-cancel/', views.payment_cancel_view, name='payment_cancel'),

    # Müşteri Panelleri
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),

    path('my-favorites/', views.my_favorites_view, name='my_favorites'),
    path('favorite/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
]