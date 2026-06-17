from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Category Name")
    slug = models.SlugField(unique=True, help_text="Unique slug for URL")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Category")
    title = models.CharField(max_length=200, verbose_name="Product Title")
    description = models.TextField(verbose_name="Product Description")

    description_features = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="2. Açıklama (Kutulara Gidecek Kurumsal Metin)"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Base Price (Smallest Size)")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Discounted Base Price")
    stock = models.IntegerField(default=0, verbose_name="Stock Quantity")
    main_image = models.ImageField(upload_to='products/main/', verbose_name="Main Image")
    video = models.FileField(upload_to='products/videos/', null=True, blank=True, verbose_name="Product Video (Optional)")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.title

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

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="User")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

    def get_total_price(self):
        return sum(item.get_item_total() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Cart")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Product")
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Selected Variant")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantity")

    def __str__(self):
        return f"{self.product.title} ({self.quantity} Pcs)"

    def get_item_total(self):
        if self.variant:
            return self.variant.price_impact * self.quantity
        base = self.product.discount_price if self.product.discount_price else self.product.price
        return base * self.quantity
    
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
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, created = Profile.objects.get_or_create(user=instance)
    profile.save()

class Order(models.Model):
    # KANKA: Kargo ve sipariş yönetim adımlarını buraya tam kurumsal dilde kilitledik!
    STATUS_CHOICES = [
        ('Pending', 'Pending Payment'),
        ('Paid', 'Paid (Preparing Product)'),   # Ürün Hazırlanıyor Aşaması
        ('Shipped', 'Shipped (On the Way)'),     # Kargoya Verildi Aşaması
        ('Completed', 'Delivered & Completed'),  # Teslim Edildi Aşaması
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
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True, verbose_name="Stripe ID")
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
    
# shop/models.py dosyasının en altına ekle kanka:

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Product")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="User")
    rating = models.PositiveIntegerField(default=5, verbose_name="Rating (1-5)")
    comment = models.TextField(verbose_name="Review Comment")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"
        ordering = ['-created_at'] # En yeni yorum en üstte görünsün kanka

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.rating}★)"