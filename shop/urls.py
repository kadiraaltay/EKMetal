from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'), # Detay sayfa linki
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'), # Sepete ekleme linki
    path('cart/', views.cart_detail, name='cart_detail'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('profile/', views.profile_view, name='profile'),
    path('checkout/', views.checkout_view, name='checkout'),

    # shop/urls.py içindeki listeye ekle kanka:
    path('payment-success/', views.payment_success_view, name='payment_success'),
    path('payment-cancel/', views.payment_cancel_view, name='payment_cancel'),

    # shop/urls.py içindeki listeye ekle kanka:
    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),
]