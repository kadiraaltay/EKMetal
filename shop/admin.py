from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, ProductImage, ProductVariant, Profile
from .models import Order, OrderItem
from .models import Review
from .models import Coupon


# ==========================================
# 1. PRODUCT & CATEGORY ADMIN AYARLARI (Senin Mevcut Yapın)
# ==========================================

# Ürün içinden direkt resim ekleyebilmek için satır içi model
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Varsayılan olarak 3 boş resim alanı açar

# Ürün içinden direkt boyut ekleyebilmek için satır içi model
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 2  # Varsayılan olarak 2 boş boyut alanı açar

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'discount_price', 'stock', 'is_active']
    inlines = [ProductImageInline, ProductVariantInline]  # Resimleri ve Boyutları ürün sayfasına gömdük


# ==========================================
# 2. USER & PROFILE INLINE AYARLARI (Yeni Akıllı Yapı)
# ==========================================

# Profil bilgilerini kullanıcının içine gömmek (inline) için kutu tasarımı kanka
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Shipping & Profile Details'
    fk_name = 'user'

# Django'nun kendi standart UserAdmin sayfasını baştan yazıyoruz kanka
class UserAdmin(BaseUserAdmin):
    # Kullanıcının içine o oluşturduğumuz profil kutusunu gömüyoruz
    inlines = (ProfileInline, )

    # Kullanıcı listesi ana ekranında senin için kritik olan sütunları ekliyoruz
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_country', 'get_city')

    # Liste ekranında kullanıcının ülkesini çekebilmek için sihirli fonksiyon kanka
    def get_country(self, instance):
        return instance.profile.country if hasattr(instance, 'profile') else ''
    get_country.short_description = 'Country'

    # Liste ekranında kullanıcının şehrini çekebilmek için sihirli fonksiyon kanka
    def get_city(self, instance):
        return instance.profile.city if hasattr(instance, 'profile') else ''
    get_city.short_description = 'City'


# 3. Eski standart User modelinin kaydını silip, bu yeni akıllı inline yapıyla tekrar sisteme tescilliyoruz kanka
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0 # Boş alan bırakma, sadece satın alınan ürünleri göster kanka
    readonly_fields = ('product', 'variant', 'quantity', 'price') # Değiştirilemez yapalım, fatura bozulmasın

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Ana listede görünecek sütunlar (İşte o durum buraya geliyor kanka!)
    list_display = ('id', 'user', 'total_price', 'status', 'country', 'city', 'created_at')
    
    # Sipariş durumuna ve ülkeye göre sağ tarafa hızlı filtre koyuyoruz kanka
    list_filter = ('status', 'country', 'created_at')
    
    # Kullanıcı adına ve şehir adına göre arama kutusu
    search_fields = ('user__username', 'first_name', 'last_name', 'city')
    
    # Siparişin içine tıkladığında alt tarafta hangi ürünleri aldığını gömülü (inline) gösteriyoruz
    inlines = [OrderItemInline]
    
    # Sipariş tarihini ve toplam fiyatı admin panelinden kazara değiştirmeyelim diye salt okunur yapıyoruz
    readonly_fields = ('created_at', 'total_price', 'stripe_payment_intent')

admin.site.register(Review)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['code']