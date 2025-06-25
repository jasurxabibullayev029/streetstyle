from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    orders_count = models.IntegerField(default=0)
    bonus_points = models.IntegerField(default=0)
    phone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} profili"

class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    card_number = models.CharField(max_length=19)  # 1234 5678 9012 3456 format
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Kutilmoqda'),
        ('completed', 'Muvaffaqiyatli'),
        ('failed', 'Xatolik'),
    ], default='pending')
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} so'm"
    
    def save(self, *args, **kwargs):
        # Agar to'lov muvaffaqiyatli bo'lsa, foydalanuvchi balansiga qo'shamiz
        if self.status == 'completed' and self.pk is None:
            profile, created = UserProfile.objects.get_or_create(user=self.user)
            profile.balance += self.amount
            profile.save()
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    back_image = models.ImageField(upload_to='products/back/', blank=True, null=True)

    def __str__(self):
        return self.name

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Kutilmoqda'),
        ('processing', 'Jarayonda'),
        ('shipped', 'Yuborildi'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilindi'),
    ], default='pending')
    
    def __str__(self):
        return f"{self.user.username} - {self.total_amount} so'm"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.size})"
