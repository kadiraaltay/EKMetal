import io
import json
import base64
import hmac
import hashlib
import requests
import random
import string
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Category, Product, ProductImage, ProductVariant, Order, OrderItem, Review, Favorite, Cart, CartItem, Profile, Coupon

# ==================== PAYTR API MOTORU (TEST MODU AKTİF) ====================
# PayTR'a bireysel başvuru yapınca panelinden alacağın canlı keyleri settings.py'a ekleyebilirsin kanka.
PAYTR_MERCHANT_ID = getattr(settings, 'PAYTR_MERCHANT_ID', '123456')
PAYTR_MERCHANT_KEY = getattr(settings, 'PAYTR_MERCHANT_KEY', 'XXXXXX_TEST_KEY_XXXXXX')
PAYTR_MERCHANT_SALT = getattr(settings, 'PAYTR_MERCHANT_SALT', 'XXXXXX_TEST_SALT_XXXXXX')

# ==================== ANA SAYFA VE ARAMA MOTORU ====================
def index(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        products = products.order_by('discount_price', 'price')
    elif sort_by == 'price_high':
        products = products.order_by('-discount_price', '-price')
    else:
        products = products.order_by('-created_at')

    context = {
        'products': products,
        'categories': categories,
        'current_sort': sort_by,
        'current_category': category_slug,
        'current_query': query,
    }
    return render(request, 'shop/index.html', context)

# ==================== ÜRÜN DETAY VE YORUM SİSTEMİ ====================
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    can_review = False
    
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__status__in=['Paid', 'Shipped', 'Completed'],
            product=product
        ).exists()

    reviews = product.reviews.all()

    if request.method == 'POST' and can_review:
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '').strip()
        review_image = request.FILES.get('review_image')
        
        if comment:
            existing_review = Review.objects.filter(product=product, user=request.user).first()
            
            if existing_review:
                existing_review.rating = int(rating)
                existing_review.comment = comment
                if review_image:
                    existing_review.image = review_image
                existing_review.save()
                messages.success(request, "Your review has been updated successfully.")
            else:
                Review.objects.create(
                    product=product,
                    user=request.user,
                    rating=int(rating),
                    comment=comment,
                    image=review_image
                )
                messages.success(request, "Thank you! Your review has been published successfully.")
                
            return redirect('product_detail', pk=product.pk)

    context = {
        'product': product,
        'can_review': can_review,
        'reviews': reviews
    }
    return render(request, 'shop/product_detail.html', context)

# ==================== SEPET İŞLEMLERİ SİSTEMİ ====================
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to add items to your cart.")
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant')
    
    variant = None
    if variant_id and variant_id != "0":
        variant = ProductVariant.objects.filter(product=product, id=variant_id).first()

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant
    )
    
    if not item_created:
        cart_item.quantity += 1
    cart_item.save()
    
    return redirect('cart_detail')


def cart_detail(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'shop/cart_detail.html', {'cart': cart})


def update_cart_quantity(request, item_id):
    if request.method == 'POST' and request.user.is_authenticated:
        data = json.loads(request.body)
        action = data.get('action')
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if action == 'increase':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                return JsonResponse({
                    'deleted': True, 
                    'cart_subtotal': 0.00,
                    'discount_amount': 0.00,
                    'cart_total': 0.00
                })
                
        cart = request.user.cart
        return JsonResponse({
            'quantity': int(cart_item.quantity),
            'item_total': float(cart_item.get_item_total()),
            'cart_subtotal': float(cart.get_subtotal_price()),
            'discount_amount': float(cart.get_discount_amount()),
            'cart_total': float(cart.get_total_price())
        })
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)

def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(id=item_id, cart__user=request.user).first()
        if cart_item:
            cart_item.delete()
    return redirect('cart_detail')

# ==================== KULLANICI KAYIT / GİRİŞ SİSTEMİ ====================
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, "Harika! Kayıt işleminiz başarılı. İlk siparişinize özel %10 indirim kodunuz: EKMETAL10")
            return redirect('cart_detail')
    else:
        form = UserCreationForm()
        
    return render(request, 'shop/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('cart_detail')
    else:
        form = AuthenticationForm()
        
    return render(request, 'shop/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('index')

# ==================== PROFiL VE ADRES YÖNETİMİ ====================
@login_required(login_url='/login/')
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()
        
        profile.phone_code = request.POST.get('phone_code', '').strip()
        profile.phone_number = request.POST.get('phone_number', '').strip()
        profile.country = request.POST.get('country', '').strip()
        profile.state = request.POST.get('state', '').strip()
        profile.city = request.POST.get('city', '').strip()
        profile.zip_code = request.POST.get('zip_code', '').strip()
        profile.address_line = request.POST.get('address_line', '').strip()
        profile.save()
        
        messages.success(request, 'Your profile address details have been successfully updated!')
        return redirect('profile')
        
    return render(request, 'shop/profile.html', {'profile': profile})

# ==================== PAYTR CHECKOUT MANAGEMENT ====================
@login_required(login_url='/login/')
def paytr_checkout_view(request):
    try:
        cart = request.user.cart
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty!")
        return redirect('cart_detail')
        
    if not cart.items.exists():
        messages.error(request, "Your cart is empty!")
        return redirect('cart_detail')
        
    profile = request.user.profile
    total_price = cart.get_total_price()
    
    if request.method == 'POST':
        address_line = request.POST.get('address_line')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')
        
        # 1. Sipariş kaydını oluşturuyoruz kanka
        order = Order.objects.create(
            user=request.user,
            first_name=request.user.first_name or "Kadir",
            last_name=request.user.last_name or "Altay",
            phone_code=profile.phone_code or "+90",
            phone_number=profile.phone_number or "5555555555",
            country=profile.country or "Türkiye",
            state=state,
            city=city,
            zip_code=zip_code,
            address_line=address_line,
            total_price=total_price,
            status='Pending'
        )
        
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.variant.price_impact if item.variant else (item.product.discount_price if item.product.discount_price else item.product.price)
            )

        # 2. PayTR Parametrelerini Hazırlıyoruz
        merchant_oid = str(order.id)
        user_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_email = request.user.email or "kadiraltay90@gmail.com"
        
        # PayTR tutarı kuruş cinsinden tamsayı olarak ister kanka
        payment_amount = int(total_price * 100)
        
        user_name = f"{order.first_name} {order.last_name}"
        user_address = f"{order.address_line} {order.city} {order.state} {order.zip_code}"
        user_phone = order.phone_number
        
        # Başarı ve Hata sayfaları yönlendirme linkleri
        merchant_ok_url = request.build_absolute_uri('/payment-success/') + f'?order_id={order.id}'
        merchant_fail_url = request.build_absolute_uri('/payment-cancel/')
        
        # Sepet içeriğini PayTR formatına (JSON Array) çeviriyoruz
        basket_items = []
        for item in cart.items.all():
            item_price = str(item.variant.price_impact if item.variant else (item.product.discount_price if item.product.discount_price else item.product.price))
            basket_items.append([item.product.title[:20], item_price, item.quantity])
            
        user_basket = base64.b64encode(json.dumps(basket_items).encode('utf-8')).decode('utf-8')
        
        # Taksit ve Döviz Konfigürasyonları
        no_installment = '1'  # 1: Taksit yapılmasın (Bireysel POS için ideal kanka)
        max_installments = '1'
        currency = 'TL'       # İstek türü varsayılan TL (Yurtdışı kartları da bu tutardan çevrilir kanka)
        test_mode = '1'       # 1: Test ortamı aktif. Canlıya geçince '0' yaparsın.

        # 3. PayTR Token Şifreleme (SHA256 Hash Yapısı kanka)
        hash_str = PAYTR_MERCHANT_ID + user_ip + merchant_oid + user_email + str(payment_amount) + user_basket + no_installment + max_installments + currency + test_mode
        paytr_token = hmac.new(PAYTR_MERCHANT_KEY.encode('utf-8'), (hash_str + PAYTR_MERCHANT_SALT).encode('utf-8'), hashlib.sha256).digest()
        token = base64.b64encode(paytr_token).decode('utf-8')

        params = {
            'merchant_id': PAYTR_MERCHANT_ID,
            'user_ip': user_ip,
            'merchant_oid': merchant_oid,
            'email': user_email,
            'payment_amount': payment_amount,
            'paytr_token': token,
            'user_basket': user_basket,
            'user_name': user_name,
            'user_address': user_address,
            'user_phone': user_phone,
            'merchant_ok_url': merchant_ok_url,
            'merchant_fail_url': merchant_fail_url,
            'no_installment': no_installment,
            'max_installments': max_installments,
            'currency': currency,
            'test_mode': test_mode
        }
        
        try:
            # PayTR Sunucusundan iFrame Ödeme token'ını talep ediyoruz
            response = requests.post('https://www.paytr.com/odeme/api/get-token', data=params, timeout=5)
            res_json = response.json()
            
            if res_json['status'] == 'success':
                context = {
                    'iframe_token': res_json['token'],
                    'order': order
                }
                # Müşteriyi PayTR iFrame ödeme şablonuna paslıyoruz kanka
                return render(request, 'shop/paytr_checkout.html', context)
            else:
                messages.error(request, f"PayTR Token Hatası: {res_json.get('reason')}")
                order.delete()
                return redirect('checkout')
                
        except Exception as e:
            messages.error(request, f"PayTR Bağlantı Hatası: {str(e)}")
            order.delete()
            return redirect('checkout')
            
    context = {
        'cart': cart,
        'profile': profile,
        'total_price': total_price
    }
    return render(request, 'shop/checkout.html', context)

# ==================== KURUMSAL ADRES VE FATURA MOTORU ====================
def send_invoice_pdf_email(order, request):
    try:
        context = {'order': order}
        html_string = render_to_string('shop/invoice_pdf.html', context)
        pdf_buffer = io.BytesIO()
        
        pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
        
        if not pisa_status.err:
            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.getvalue()
            
            subject = f"Your EK Metal Wall Art Invoice - Order #{order.id}"
            message = render_to_string('shop/invoice_email_text.html', {'order': order})
            recipient_list = [order.user.email if order.user and order.user.email else request.user.email]
            
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list
            )
            email.attach(f"EKMetal_Invoice_{order.id}.pdf", pdf_data, "application/pdf")
            email.send(fail_silently=False)
            print(f"--- EMAIL SUCCESS: Invoice for Order #{order.id} sent successfully! ---")
            
    except Exception as email_error:
        print(f"--- EMAIL ERROR: Invoice email could not be sent. Details: {email_error} ---")

# ==================== PAYTR GÜVENLİ BİLDİRİM SERVİSİ (CALLBACK) ====================
# Ödeme tamamlandığında PayTR sunucuları sitemize arkadan bu POST isteğini atar kanka.
@csrf_exempt
def paytr_callback_view(request):
    if request.method == 'POST':
        merchant_oid = request.POST.get('merchant_oid')
        status = request.POST.get('status')
        total_amount = request.POST.get('total_amount')
        hash_received = request.POST.get('hash')

        # Gelen isteğin doğruluğunu hash eşleşmesiyle kontrol ediyoruz kanka (Güvenlik Duvarı)
        hash_str = merchant_oid + PAYTR_MERCHANT_SALT + status + total_amount
        paytr_token = hmac.new(PAYTR_MERCHANT_KEY.encode('utf-8'), hash_str.encode('utf-8'), hashlib.sha256).digest()
        token = base64.b64encode(paytr_token).decode('utf-8')

        if token != hash_received:
            return HttpResponse("FAIL: Bad Hash")

        try:
            order = Order.objects.get(id=int(merchant_oid))
            
            if status == 'success':
                order.status = 'Paid'  # Siparişi ödendi olarak işaretle kanka
                order.save()
                
                # Faturayı arka planda oluşturup e-posta gönder kanka
                send_invoice_pdf_email(order, request)
                
                # Ödeme başarılı olduğu için kullanıcının sepetini uçur kanka
                try:
                    order.user.cart.items.all().delete()
                except:
                    pass
                
                return HttpResponse("OK")
            else:
                order.status = 'Failed'
                order.save()
                return HttpResponse("OK")  # Hata olsa da PayTR'a OK demeliyiz yoksa sürekli istek atar.
                
        except Order.DoesNotExist:
            return HttpResponse("FAIL: Order Not Found")
            
    return HttpResponse("Geçersiz İstek Kanka!")

# ==================== PAYTR BAŞARI SAYFASI ====================
def payment_success_view(request):
    order_id = request.GET.get('order_id')
    order = None
    if order_id:
        order = Order.objects.filter(id=order_id).first()
    return render(request, 'shop/payment_success.html', {'order_id': order_id, 'order': order})


def payment_cancel_view(request):
    return render(request, 'shop/payment_cancel.html')

# ==================== MÜŞTERI PANELİ PANORAMALARI ====================
@login_required(login_url='/login/')
def my_orders_view(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'shop/my_orders.html', {'orders': orders})


@login_required(login_url='/login/')
def my_reviews_view(request):
    return render(request, 'shop/my_reviews.html', {'reviews': request.user.reviews.all()})

# ==================== KUPON YÖNETİM SİSTEMİ ====================
def apply_coupon(request):
    if request.method == "POST":
        code = request.POST.get('coupon_code', '').strip()
        cart = get_object_or_404(Cart, user=request.user)
        
        coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
        
        if coupon:
            cart.coupon = coupon
            cart.save()
            messages.success(request, f"Kupon başarıyla uygulandı! %{coupon.discount_percent} indirim kazandınız.")
        else:
            messages.error(request, "Geçersiz veya süresi dolmuş kupon kodu kanka!")
            
    return redirect('cart_detail')


def remove_coupon(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.coupon = None
    cart.save()
    messages.info(request, "Kupon kaldırıldı.")
    return redirect('cart_detail')


@login_required(login_url='/login/')
def my_favorites_view(request):
    favorites = request.user.favorites.all().order_by('-created_at')
    return render(request, 'shop/my_favorites.html', {'favorites': favorites})

@login_required(login_url='/login/')
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    fav_exists = Favorite.objects.filter(user=request.user, product=product).first()
    
    if fav_exists:
        fav_exists.delete()
        messages.success(request, "Product removed from your favorites.")
    else:
        Favorite.objects.create(user=request.user, product=product)
        messages.success(request, "Product added to your favorites.")
        
    return redirect(request.META.get('HTTP_REFERER', 'my_favorites'))

# shop/views.py en altına yapıştır kanka:
def privacy_policy_view(request):
    return render(request, 'shop/privacy_policy.html')

def terms_of_sale_view(request):
    return render(request, 'shop/terms_of_sale.html')

def return_policy_view(request):
    return render(request, 'shop/return_policy.html')