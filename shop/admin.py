from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
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
# 2. USER & PROFILE ORİJİNAL AYARI
# ==========================================

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, )
    # Kanka CSS'i patlatan o sanal get_country/get_city alanlarını listeden kaldırdım, 
    # profil detayları zaten kullanıcının içine tıklayınca altta tertemiz açılıyor!
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# ==========================================
# 3. SHOP & ORDER ORİJİNAL AYARLARI
# ==========================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'discount_price', 'stock', 'is_active']
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Ana listeyi sadece gerçek veritabanı alanlarıyla sınırlandırdık, kayma riski sıfırlandı
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