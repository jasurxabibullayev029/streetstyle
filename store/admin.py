from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Product, Order, OrderItem

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_balance', 'get_orders_count', 'get_bonus_points', 'is_staff')
    
    def get_balance(self, obj):
        return obj.profile.balance if hasattr(obj, 'profile') else 0.00
    get_balance.short_description = 'Balans'
    
    def get_orders_count(self, obj):
        return obj.profile.orders_count if hasattr(obj, 'profile') else 0
    get_orders_count.short_description = 'Buyurtmalar'
    
    def get_bonus_points(self, obj):
        return obj.profile.bonus_points if hasattr(obj, 'profile') else 0
    get_bonus_points.short_description = 'Bonus ballar'

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'has_back_image')
    list_filter = ('price',)
    search_fields = ('name',)
    
    def has_back_image(self, obj):
        return bool(obj.back_image)
    has_back_image.boolean = True
    has_back_image.short_description = 'Orqa tomon rasm'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_ordered_products', 'get_user_info', 'get_user_phone', 'get_user_balance', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__profile__phone')
    inlines = [OrderItemInline]
    
    def get_ordered_products(self, obj):
        items = obj.items.all()
        if items:
            product_list = []
            for item in items:
                product_info = f"{item.product.name}"
                if item.quantity > 1:
                    product_info += f" x{item.quantity}"
                if item.size:
                    product_info += f" ({item.size})"
                product_list.append(product_info)
            return ", ".join(product_list)
        return "Mahsulot yo'q"
    get_ordered_products.short_description = 'Zakaz qilingan mahsulotlar'
    
    def get_user_info(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
        return "N/A"
    get_user_info.short_description = 'Foydalanuvchi'
    
    def get_user_phone(self, obj):
        if obj.user and hasattr(obj.user, 'profile') and obj.user.profile.phone:
            return obj.user.profile.phone
        return "Telefon yo'q"
    get_user_phone.short_description = 'Telefon'
    
    def get_user_balance(self, obj):
        if obj.user and hasattr(obj.user, 'profile'):
            return f"{obj.user.profile.balance} so'm"
        return "0.00 so'm"
    get_user_balance.short_description = 'Balans'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'user__profile').prefetch_related('items__product')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
