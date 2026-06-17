from .models import Cart

def cart_item_count(request):
    # Eğer kullanıcı giriş yapmadıysa sepet sayısı 0'dır
    if not request.user.is_authenticated:
        return {'cart_items_total': 0}
        
    try:
        # Kullanıcının sepetini bul ve içindeki tüm ürünlerin adetlerini topla
        cart = Cart.objects.get(user=request.user)
        total_items = sum(item.quantity for item in cart.items.all())
        return {'cart_items_total': total_items}
    except Cart.DoesNotExist:
        return {'cart_items_total': 0}