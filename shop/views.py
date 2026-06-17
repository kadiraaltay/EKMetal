import io
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Cart, CartItem, ProductVariant, Profile, Order, OrderItem
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cart, Order, OrderItem, Review

# Stripe gizli anahtarını sisteme tanıtıyoruz kanka
stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    # Sitedeki tüm aktif ürünleri ve kategorileri çekiyoruz
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    # 1. ARAMA ÖZELLİĞİ (Search)
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # 2. KATEGORİ FİLTRELEME
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # 3. SIRALAMA ÖZELLİĞİ (Fiyat vb.)
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

# shop/views.py içindeki product_detail fonksiyonunu bununla değiştir kanka:

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # Varsayılan olarak kullanıcının yorum yapma hakkı yok diyoruz kanka
    can_review = False
    
    if request.user.is_authenticated:
        # Kullanıcının 'Paid', 'Shipped' veya 'Completed' durumundaki siparişlerinde bu ürün var mı diye bakıyoruz
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status__in=['Paid', 'Shipped', 'Completed'],
            product=product
        ).exists()
        
        if has_purchased:
            can_review = True

    # Ürüne gelen tüm yorumları çekiyoruz
    reviews = product.reviews.all()

    # Eğer yorum yazıp POST attıysa onu yakalıyoruz kanka
    if request.method == 'POST' and can_review:
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment', '').strip()
        
        if comment:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=int(rating),
                comment=comment
            )
            messages.success(request, "Thank you! Your review has been published successfully.")
            return redirect('product_detail', pk=product.pk)

    context = {
        'product': product,
        'can_review': can_review,
        'reviews': reviews
    }
    return render(request, 'shop/product_detail.html', context)

# 1. SEPETE ÜRÜN EKLEME FONKSİYONU
def add_to_cart(request, product_id):
    # KANKA: Giriş yapmadıysa artık admin paneline DEĞİL, kendi login sayfamıza fırlatıyoruz!
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to add items to your cart.")
        return redirect('login')
    
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant')
    
    variant = None
    if variant_id and variant_id != "0":
        variant = ProductVariant.objects.filter(product=product, price_impact=variant_id).first()

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant
    )
    
    if not item_created:
        cart_item.quantity += 1
    cart_item.save()
    
    return redirect('cart_detail')

# 2. SEPET DETAY SAYFASI FONKSİYONU
def cart_detail(request):
    # KANKA: Sepete tıklayan üye değilse yine admin yerine bizim şık üye giriş sayfasına gidiyor!
    if not request.user.is_authenticated:
        return redirect('login')
        
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'shop/cart_detail.html', {'cart': cart})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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

def update_cart_quantity(request, item_id):
    if request.method == 'POST' and request.user.is_authenticated:
        import json
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
                return JsonResponse({'deleted': True, 'cart_total': request.user.cart.get_total_price()})
                
        return JsonResponse({
            'quantity': cart_item.quantity,
            'item_total': cart_item.get_item_total(),
            'cart_total': cart_item.cart.get_total_price()
        })
    return JsonResponse({'error': 'Geçersiz istek'}, status=400)

def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
    return redirect('cart_detail')

@login_required(login_url='/login/')
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone_code = request.POST.get('phone_code', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        country = request.POST.get('country', '').strip()
        state = request.POST.get('state', '').strip()
        city = request.POST.get('city', '').strip()
        zip_code = request.POST.get('zip_code', '').strip()
        address_line = request.POST.get('address_line', '').strip()
        
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        profile.phone_code = phone_code
        profile.phone_number = phone_number
        profile.country = country
        profile.state = state
        profile.city = city
        profile.zip_code = zip_code
        profile.address_line = address_line
        profile.save()
        
        messages.success(request, 'Your profile address details have been successfully updated!')
        return redirect('profile')
        
    return render(request, 'shop/profile.html', {'profile': profile})

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
            first_name=request.user.first_name,
            last_name=request.user.last_name,
            phone_code=profile.phone_code,
            phone_number=profile.phone_number,
            country=profile.country,
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
            
        stripe_total = int(total_price * 100)
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"Order #{order.id} - EK Metal Wall Art",
                            },
                            'unit_amount': stripe_total,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/payment-success/') + f'?session_id={{CHECKOUT_SESSION_ID}}&order_id={order.id}',
                cancel_url=request.build_absolute_uri('/payment-cancel/'),
            )
            
            order.stripe_payment_intent = checkout_session.id
            order.save()
            
            return redirect(checkout_session.url, code=303)
            
        except Exception as e:
            messages.error(request, f"Stripe Error: {str(e)}")
            order.delete()
            return redirect('checkout')
            
    context = {
        'cart': cart,
        'profile': profile,
        'total_price': total_price
    }
    return render(request, 'shop/checkout.html', context)

def payment_success_view(request):
    session_id = request.GET.get('session_id')
    order_id = request.GET.get('order_id')
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if order.status == 'Pending':
                order.status = 'Paid'
                order.save()
                
                # 1. AŞAMA: PDF Faturayı Hafızada Oluşturuyoruz kanka
                context = {'order': order}
                html_string = render_to_string('shop/invoice_pdf.html', context)
                pdf_buffer = io.BytesIO()
                
                # HTML'i PDF'e çevir kanka
                pisa_status = pisa.CreatePDF(html_string, dest=pdf_buffer)
                
                if not pisa_status.err:
                    pdf_buffer.seek(0)
                    pdf_data = pdf_buffer.getvalue()
                    
                    # 2. AŞAMA: Müşteriye E-posta Gönderimi
                    subject = f"Your EK Metal Wall Art Invoice - Order #{order.id}"
                    message = render_to_string('shop/invoice_email_text.html', {'order': order})
                    recipient_list = [request.user.email]
                    
                    email = EmailMessage(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        recipient_list
                    )
                    # Hazırladığımız PDF'i maile ek olarak koyuyoruz kanka!
                    email.attach(f"EKMetal_Invoice_{order.id}.pdf", pdf_data, "application/pdf")
                    email.send(fail_silently=True)
                
                # 3. AŞAMA: Ödeme bittiği için sepeti temizle kanka
                try:
                    cart = request.user.cart
                    cart.items.all().delete()
                except Cart.DoesNotExist:
                    pass
        except Order.DoesNotExist:
            return redirect('index')
            
    return render(request, 'shop/payment_success.html', {'order_id': order_id})
    
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if order.status == 'Pending':
                order.status = 'Paid'
                order.save()
                try:
                    cart = request.user.cart
                    cart.items.all().delete()
                except Cart.DoesNotExist:
                    pass
        except Order.DoesNotExist:
            return redirect('index')
            
    return render(request, 'shop/payment_success.html', {'order_id': order_id})

def payment_cancel_view(request):
    return render(request, 'shop/payment_cancel.html')

@login_required(login_url='/login/')
def my_orders_view(request):
    orders = request.user.orders.all().order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'shop/my_orders.html', context)