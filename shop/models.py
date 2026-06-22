from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

# ==========================================
# 1. KATEGORİ VE KUPON MODELLERİ
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(unique=True, help_text="Unique slug for URL")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Kupon Kodu")
    discount_percent = models.PositiveIntegerField(
        default=10, 
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name="İndirim Oranı (%)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} (-%{self.discount_percent})"


# ==========================================
# 2. ÜRÜN VE VARYANT MODELLERİ
# ==========================================

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Category")
    title = models.CharField(max_length=200, verbose_name="Product Title")
    description = models.TextField(verbose_name="Product Description")
    description_features = models.TextField(blank=True, null=True, verbose_name="2. Açıklama (Kutulara Gidecek Kurumsal Metin)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Base Price (Smallest Size)")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Discounted Base Price")
    stock = models.IntegerField(default=0, verbose_name="Stock Quantity")
    main_image = models.ImageField(upload_to='products/main/', verbose_name="Main Image")
    video = models.FileField(upload_to='products/videos/', null=True, blank=True, verbose_name="Product Video (Optional)")
    seo_keywords = models.CharField(max_length=500, blank=True, null=True, verbose_name="SEO Anahtar Kelimeler")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.title

    # ⚡ KANKA: Ürünün indirim yüzdesini dinamik hesaplayan fonksiyon
    def get_discount_percent(self):
        if self.discount_price and self.price > 0:
            percent = ((self.price - self.discount_price) / self.price) * 100
            return int(round(percent))
        return 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Product")
    image = models.ImageField(upload_to='products/gallery/', verbose_name="Gallery Image")

    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Product")
    size = models.CharField(max_length=50, help_text="e.g., 20x28 inches, 40x60 inches", verbose_name="Size / Dimensions")
    price_impact = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Price Impact (+$)")

    class Meta:
        verbose_name = "Product Size Variant"
        verbose_name_plural = "Product Size Variants"

    def __str__(self):
        return f"{self.product.title} - {self.size} (+${self.price_impact})"

    # ⚡ KANKA: İstediğin gibi, ürünün diğer tüm ölçülerine (boyut varyantlarına) indirimi otomatik yansıtan canavar fonksiyon
    def get_variant_prices(self):
        discount_percent = self.product.get_discount_percent()
        original_variant_price = self.price_impact
        
        if discount_percent > 0:
            # Varyantın kendi fiyatına da aynı indirim oranını çakıyoruz kanka
            discount_amount = (original_variant_price * discount_percent) / 100
            discounted_variant_price = original_variant_price - discount_amount
            return {
                'is_discounted': True,
                'original': original_variant_price,
                'discounted': discounted_variant_price,
                'percent': discount_percent
            }
        return {
            'is_discounted': False,
            'original': original_variant_price,
            'discounted': original_variant_price,
            'percent': 0
        }


# ==========================================
# 3. SEPET MODELLERİ
# ==========================================

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="User")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Uygulanan Kupon")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def get_subtotal_price(self):
        return sum(item.get_item_total() for item in self.items.all())

    def get_discount_amount(self):
        subtotal = self.get_subtotal_price()
        if self.coupon:
            return (subtotal * self.coupon.discount_percent) / 100
        return 0

    def get_total_price(self):
        subtotal = self.get_subtotal_price()
        discount = self.get_discount_amount()
        return max(0, subtotal - discount)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Product")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Selected Variant")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    def __str__(self):
        return f"{self.product.title} ({self.quantity} Pcs)"

    def get_item_total(self):
        # ⚡ KANKA: Sepette de indirimli varyant fiyatlarının geçerli olmasını sağladık
        if self.variant:
            prices = self.variant.get_variant_prices()
            return prices['discounted'] * self.quantity
            
        base_price = self.product.discount_price if self.product.discount_price else self.product.price
        return base_price * self.quantity


# ==========================================
# 4. SİPARİŞ VE YORUM MODELLERİ
# ==========================================

class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending Payment'),
        ('Paid', 'Paid (Preparing Product)'),
        ('Shipped', 'Shipped (On the Way)'),
        ('Completed', 'Delivered & Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_code = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    address_line = models.TextField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    iyzico_payment_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="iyzico Payment ID")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x {self.quantity} (Order #{self.order.id})"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Product")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="User")
    rating = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Rating (1-5)")
    comment = models.TextField(verbose_name="Review Comment")
    image = models.ImageField(upload_to='reviews/', blank=True, null=True, verbose_name="Review Image")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating}★)"


# ==========================================
# 5. PROFİL VE SİNYALLER (SIGNALS)
# ==========================================

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile') 
    phone_code = models.CharField(max_length=10, blank=True, null=True, default='+1')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name="State / Region")
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="ZIP / Postal Code")
    address_line = models.TextField(blank=True, null=True, verbose_name="Full Address")

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    if not created:
        profile.save()


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name="User")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by', verbose_name="Product")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"