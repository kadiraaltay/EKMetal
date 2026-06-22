from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.safestring import mark_safe
from .models import Category, Coupon, Product, ProductImage, ProductVariant, Profile, Order, OrderItem, Review, Cart, CartItem

# ==========================================
# 1. INLINE (SATIR İÇİ) YAPILAR
# ==========================================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 2

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'quantity', 'price')

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Shipping & Profile Details'
    fk_name = 'user'

# ==========================================
# 2. USER & PROFILE AYARI
# ==========================================

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ==========================================
# 3. SHOP & ORDER AYARLARI (BEDAVA DESTEKLİ MOTOR)
# ==========================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'discount_price', 'stock', 'is_active']
    search_fields = ['title', 'description', 'seo_keywords']
    inlines = [ProductImageInline, ProductVariantInline]
    
    def changelist_view(self, request, extra_context=None):
        storage = messages.get_messages(request)
        for _ in storage: pass  # Eski mesajları temizle
        
        # Kutunun içinde 33 takılı kalmasın diye güncel yüzdeyi çekiyoruz kanka
        current_percent = 0
        first_product = Product.objects.all().first()
        
        # Eğer indirimli fiyat None değilse ve fiyata eşit değilse indirim yüzdesini hesapla
        if first_product and first_product.discount_price is not None:
            # discount_price 0.00 olduğunda (%100 indirim) percent 100 kalacak kanka
            if first_product.discount_price == 0:
                current_percent = 100
            else:
                current_percent = first_product.get_discount_percent()

        custom_form = mark_safe(
            '<div style="background: #2c3e50; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 5px solid #e67e22;">'
                '<form method="POST" action="apply-percent-discount/" style="display: flex; align-items: center; gap: 15px;">'
                    f'<input type="hidden" name="csrfmiddlewaretoken" value="{request.META.get("CSRF_COOKIE", "")}">'
                    '<span style="color: #fff; font-weight: bold; font-size: 14px;">⚡ TÜM ÜRÜNLERE TOPLU İNDİRİM:</span>'
                    '<span style="color: #eee;">İndirim Oranı (%):</span>'
                    f'<input type="number" name="discount_percent" value="{current_percent}" min="0" max="100" style="padding: 6px; width: 70px; border-radius: 4px; border: 1px solid #ccc; font-weight: bold; text-align: center; color: #000;" required>'
                    '<span style="color: #cbd5e1; font-size: 12px;">(Kaldırmak için 0 yaz, Bedava yapmak için 100 yaz kanka)</span>'
                    '<button type="submit" style="background: #e67e22; color: white; padding: 7px 15px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">Uygula / Sıfırla 🚀</button>'
                '</form>'
            '</div>'
        )
        messages.info(request, custom_form)
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('apply-percent-discount/', self.admin_site.admin_view(self.apply_percent_discount_view), name='apply-percent-discount'),
        ]
        return custom_urls + urls

    # 🚀 KANKA: 100 yazınca bedava yapan, 0 yazınca indirim kaldıran motor kanka
    def apply_percent_discount_view(self, request):
        if request.method == 'POST':
            try:
                percent = int(request.POST.get('discount_percent', 0))
                if not (0 <= percent <= 100):
                    raise ValueError()
                
                products = Product.objects.all()
                updated_count = 0
                
                for product in products:
                    # ⚡ KANKA: Sadece 0 yazınca indirim tamamen kalkar
                    if percent == 0:
                        product.discount_price = None
                    # ⚡ KANKA: 100 yazınca indirimli fiyatı kuruşu kuruşuna 0 yapar (Bedava kanka!)
                    elif percent == 100:
                        product.discount_price = 0.00
                    # 1-99 arası ise normal yüzde indirimi basar
                    else:
                        discount_amount = (product.price * percent) / 100
                        product.discount_price = product.price - discount_amount
                    
                    product.save()
                    updated_count += 1
                
                if percent == 0:
                    self.message_user(request, f"Kanka indirim sezonu bitti. Tüm {updated_count} ürün orijinal fiyatına döndü. 🛑", messages.SUCCESS)
                elif percent == 100:
                    self.message_user(request, f"🚀 EFSANE KAMPANYA! Sitedeki tüm {updated_count} ürün şu an TAMAMEN BEDAVA yapıldı! 🔥", messages.SUCCESS)
                else:
                    self.message_user(request, f"Kanka harika! Sitedeki tüm {updated_count} ürüne birden %{percent} indirim başarıyla basıldı. 🚀", messages.SUCCESS)
                    
            except ValueError:
                self.message_user(request, "Kanka düzgün bir indirim oranı yaz (0-100 arası)!", messages.ERROR)
        
        return HttpResponseRedirect("../")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'first_name', 'last_name')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'total_price', 'iyzico_payment_id')

# ==========================================
# 4. DİĞER MODELLER
# ==========================================
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code']

admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(CartItem)