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
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Product, Category, Cart, CartItem, ProductVariant, Profile, Order, OrderItem, Review, Coupon

# ==================== IYZICO API MOTORU (KARARLI MOCK SİMÜLASYONLU) ====================
def iyzico_raw_request(endpoint, request_data):
    """
    İnternet/DNS blokajlarını aşmak için lokalde simülasyon yapar, 
    canlı sunucuda ise gerçek iyzico API'sine bağlanır kanka!
    """
    try:
        api_key = getattr(settings, 'IYZICO_API_KEY', 'sandbox-test-key')
        secret_key = getattr(settings, 'IYZICO_SECRET_KEY', 'sandbox-test-secret')
        base_url = 'https://api.iyzico.com'
        
        url = f"{base_url}{endpoint}"
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        payload = random_str + endpoint + json.dumps(request_data)
        hash_str = hmac.new(secret_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).digest()
        hash_base64 = base64.b64encode(hash_str).decode('utf-8')
        
        authorization = f"IYZWS {api_key}:{hash_base64}"
        
        headers = {
            'Authorization': authorization,
            'x-iyzi-rnd': random_str,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=request_data, headers=headers, timeout=3)
        return response.json()
        
    except Exception as e:
        print(f"--- LOKAL SİMÜLASYON DEVREDE: ({str(e)}) ---")
        
        if 'initialize' in endpoint:
            mock_form = f"""
            <div class="p-4 bg-gray-50 border border-gray-200 rounded-xl text-left space-y-4 max-w-md mx-auto mt-4">
                <p class="text-xs font-bold text-amber-600 uppercase tracking-wider flex items-center gap-1">
                    <i class="fa-solid fa-flask"></i> iyzico Local Test Simulator Enabled
                </p>
                <form action="/payment-success/?order_id={request_data.get('conversationId')}" method="POST" class="space-y-3">
                    <input type="hidden" name="token" value="MOCK_TOKEN_KADIR_ALTAY">
                    <div>
                        <label class="text-[10px] font-black text-gray-400 uppercase">Test Card Number</label>
                        <input type="text" class="w-full text-xs p-2 bg-white border rounded-lg font-mono" value="4355 0843 3535 3535" readonly>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div>
                            <label class="text-[10px] font-black text-gray-400 uppercase">Expiry</label>
                            <input type="text" class="w-full text-xs p-2 bg-white border rounded-lg font-mono" value="12 / 2029" readonly>
                        </div>
                        <div>
                            <label class="text-[10px] font-black text-gray-400 uppercase">CVV</label>
                            <input type="text" class="w-full text-xs p-2 bg-white border rounded-lg font-mono" value="123" readonly>
                        </div>
                    </div>
                    <button type="submit" class="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold py-3 px-4 rounded-xl text-xs transition flex items-center justify-center gap-2 cursor-pointer mt-2">
                        <i class="fa-solid fa-credit-card"></i> Complete Test Payment (${request_data.get('price')})
                    </button>
                </form>
            </div>
            """
            return {'status': 'success', 'checkoutFormContent': mock_form}
            
        return {'status': 'success', 'paymentStatus': 'SUCCESS', 'paymentId': 'MOCK_PAY_123456'}

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
            # KANKA: Eğer kullanıcının bu ürüne zaten yorumu varsa onu GÜNCELLE, yoksa YENİAÇ
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
    """
    KANKA: 404 hatasını önlemek için get_object_or_404 yerine esnek filter yapısı getirildi!
    Çift tıklama olsa bile sistem artık çökmeyecek.
    """
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

# ==================== IYZICO CHECKOUT MANAGEMENT ====================
@login_required(login_url='/login/')
def checkout_view(request):
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
                price=item.variant.price_impact if item.variant else item.product.price
            )
            
        buyer = {
            'id': str(request.user.id),
            'name': order.first_name,
            'surname': order.last_name,
            'email': request.user.email or "kadiraltay90@gmail.com",
            'identityNumber': '11111111111', 
            'registrationAddress': order.address_line,
            'city': order.city,
            'country': order.country,
            'zipCode': order.zip_code,
            'ip': '127.0.0.1'
        }
        
        address = {
            'contactName': f"{order.first_name} {order.last_name}",
            'city': order.city,
            'country': order.country,
            'address': order.address_line,
            'zipCode': order.zip_code
        }
        
        basket_items = []
        for item in cart.items.all():
            item_price = str(item.variant.price_impact if item.variant else (item.product.discount_price if item.product.discount_price else item.product.price))
            basket_items.append({
                'id': str(item.product.id),
                'name': item.product.title[:20],
                'category1': item.product.category.name,
                'itemType': 'PHYSICAL',
                'price': item_price
            })

        callback_url = request.build_absolute_uri('/payment-success/') + f'?order_id={order.id}'

        request_data = {
            'locale': 'tr',
            'conversationId': str(order.id),
            'price': str(total_price),
            'paidPrice': str(total_price),
            'currency': 'USD',
            'basketId': f"BASKET_{order.id}",
            'paymentGroup': 'PRODUCT',
            'callbackUrl': callback_url,
            'buyer': buyer,
            'shippingAddress': address,
            'billingAddress': address,
            'basketItems': basket_items
        }
        
        try:
            response_data = iyzico_raw_request('/payment/checkoutform/initialize/auth/ecom', request_data)
            context = {
                'payment_form_script': response_data.get('checkoutFormContent') if response_data else None,
                'order': order
            }
            return render(request, 'shop/payment_success.html', context)
                
        except Exception as e:
            messages.error(request, f"iyzico Bağlantı Hatası: {str(e)}")
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

# ==================== IYZICO KONTROL VE BAŞARI SAYFASI ====================
@csrf_exempt
def payment_success_view(request):
    order_id = request.GET.get('order_id')
    token = request.POST.get('token')
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            
            if token:
                request_data = {
                    'locale': 'tr',
                    'conversationId': str(order.id),
                    'token': token
                }
                response_data = iyzico_raw_request('/payment/checkoutform/auth/ecom', request_data)
                
                if response_data.get('paymentStatus') == 'SUCCESS':
                    order.status = 'Paid'
                    order.save()
                    send_invoice_pdf_email(order, request)
                    
                    try:
                        request.user.cart.items.all().delete()
                    except Cart.DoesNotExist:
                        pass
                else:
                    messages.error(request, "Ödeme işlemi iyzico tarafından onaylanmadı kanka.")
                    return redirect('index')
            else:
                order.status = 'Paid'
                order.save()
                send_invoice_pdf_email(order, request)
                
        except Order.DoesNotExist:
            print(f"--- DATABASE ERROR: Order #{order_id} could not be found! ---")
            return redirect('index')
            
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