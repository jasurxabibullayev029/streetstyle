from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Product, Order, OrderItem, UserProfile, Favorite, Deposit

# Create your views here.

def product_list(request):
    q = request.GET.get('q', '')
    if q:
        products = Product.objects.filter(name__icontains=q)
    else:
        products = Product.objects.all()
    
    # Get user data if logged in, otherwise use default values
    user_data = {
        'name': 'Foydalanuvchi',
        'email': 'foydalanuvchi@email.com',
        'balance': 0.00,
        'orders_count': 0,
        'bonus_points': 0
    }
    
    # Get user's favorite product IDs for like button states
    user_favorites = set()
    if request.user.is_authenticated:
        user = request.user
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Add some test data for demonstration
        if created:
            profile.balance = Decimal('125000.00')
            profile.orders_count = 8
            profile.bonus_points = 1250
            profile.save()
        
        user_data = {
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'email': user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
        
        # Get user's favorite product IDs
        user_favorites = set(Favorite.objects.filter(user=user).values_list('product_id', flat=True))
    
    context = {
        'products': products,
        'user_data': user_data,
        'user_favorites': user_favorites
    }
    
    return render(request, 'store/product_list.html', context)

def user_logout(request):
    logout(request)
    return redirect('product_list')

@require_POST
def user_register(request):
    try:
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        
        # Validate required fields
        if not all([name, email, phone, password]):
            return JsonResponse({
                'success': False,
                'error': 'Barcha maydonlarni to\'ldiring'
            })
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'Bu email allaqachon ro\'yxatdan o\'tgan'
            })
        
        # Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name.split()[0] if name else '',
            last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
        )
        
        # Create user profile
        profile = UserProfile.objects.create(
            user=user,
            phone=phone,
            balance=Decimal('0.00'),
            orders_count=0,
            bonus_points=0
        )
        
        # Log in the user
        login(request, user)
        
        return JsonResponse({
            'success': True,
            'message': 'Muvaffaqiyatli ro\'yxatdan o\'tdingiz!',
            'user_data': {
                'name': name,
                'email': email,
                'balance': '0.00',
                'orders_count': 0,
                'bonus_points': 0
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Xatolik yuz berdi: ' + str(e)
        })

@require_POST
def user_login(request):
    try:
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email va parolni kiriting'
            })
        
        # Authenticate user
        user = authenticate(username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Get user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            return JsonResponse({
                'success': True,
                'message': 'Muvaffaqiyatli kirdingiz!',
                'user_data': {
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                    'balance': str(profile.balance),
                    'orders_count': profile.orders_count,
                    'bonus_points': profile.bonus_points
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Noto\'g\'ri email yoki parol'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Xatolik yuz berdi: ' + str(e)
        })

@login_required
def my_orders(request):
    # Get user's orders with related items
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    
    # Get user profile data
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'orders': orders,
        'user_data': {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
    }
    
    return render(request, 'store/my_orders.html', context)

@login_required
def my_favorites(request):
    # Get user's favorite products
    favorites = Favorite.objects.filter(user=request.user).select_related('product').order_by('-created_at')
    
    # Get user profile data
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'favorites': favorites,
        'user_data': {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
    }
    
    return render(request, 'store/my_favorites.html', context)

@require_POST
@login_required
def toggle_favorite(request):
    try:
        product_id = request.POST.get('product_id')
        product = Product.objects.get(id=product_id)
        
        # Check if already favorited
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            # If already favorited, remove it
            favorite.delete()
            is_favorited = False
            message = 'Sevimlilardan olib tashlandi'
        else:
            # If newly favorited
            is_favorited = True
            message = 'Sevimlilarga qo\'shildi'
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'message': message
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Mahsulot topilmadi'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Xatolik yuz berdi: ' + str(e)
        })

@require_POST
@login_required
def place_order(request):
    try:
        product_id = request.POST.get('product_id')
        size = request.POST.get('size')
        quantity = int(request.POST.get('quantity', 1))
        
        # Get the product
        product = Product.objects.get(id=product_id)
        
        # Calculate total amount using Decimal
        total_amount = product.price * Decimal(quantity)
        
        # Get user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Check if user has enough balance
        if profile.balance < total_amount:
            return JsonResponse({
                'success': False,
                'error': 'Balans yetarli emas. Balansingiz: ' + str(profile.balance) + ' so\'m'
            })
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
            size=size
        )
        
        # Update user profile
        profile.balance -= total_amount
        profile.orders_count += 1
        profile.bonus_points += int(total_amount * Decimal('0.01'))  # 1% bonus
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Buyurtma muvaffaqiyatli qabul qilindi!',
            'order_id': order.id,
            'total_amount': str(total_amount),
            'new_balance': str(profile.balance),
            'new_orders_count': profile.orders_count,
            'new_bonus_points': profile.bonus_points
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Mahsulot topilmadi'
        })
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Noto\'g\'ri miqdor'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Xatolik yuz berdi: ' + str(e)
        })

@login_required
def update_profile(request):
    try:
        profile = request.user.profile
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        # Handle user information updates
        if 'first_name' in request.POST:
            request.user.first_name = request.POST.get('first_name', '').strip()
        
        if 'last_name' in request.POST:
            request.user.last_name = request.POST.get('last_name', '').strip()
        
        if 'email' in request.POST:
            email = request.POST.get('email', '').strip()
            # Check if email is already taken by another user
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Bu email allaqachon ishlatilgan'
                })
            request.user.email = email
        
        # Save user changes
        request.user.save()
        
        # Handle phone number update
        if 'phone' in request.POST:
            profile.phone = request.POST.get('phone', '').strip()
        
        profile.save()
        
        # Get updated user name for response
        user_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        
        return JsonResponse({
            'success': True,
            'message': 'Profil muvaffaqiyatli yangilandi!',
            'user_name': user_name,
            'avatar_url': profile.avatar.url if profile.avatar else None
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Xatolik yuz berdi: ' + str(e)
        })

@login_required
def profile_settings(request):
    # Get user profile data
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user_data': {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': profile.phone or '',
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
    }
    
    return render(request, 'store/profile_settings.html', context)

@login_required
def wallet(request):
    # Get user profile and orders
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    deposits = Deposit.objects.filter(user=request.user, status='completed').order_by('-created_at')
    
    # Calculate total spent
    total_spent = sum(order.total_amount for order in orders)
    
    # Calculate total deposited
    total_deposited = sum(deposit.amount for deposit in deposits)
    
    # Get recent transactions (orders and deposits)
    recent_transactions = []
    
    # Add deposit transactions
    for deposit in deposits[:5]:  # Last 5 deposits
        recent_transactions.append({
            'type': 'deposit',
            'amount': deposit.amount,
            'description': f"Karta orqali to'ldirish ({deposit.card_number})",
            'date': deposit.created_at,
            'transaction_id': f"DEP-{deposit.id}"
        })
    
    # Add spending transactions
    for order in orders[:5]:  # Last 5 orders
        for item in order.items.all():
            recent_transactions.append({
                'type': 'spending',
                'amount': item.price * item.quantity,
                'description': f"{item.product.name} ({item.size}) x{item.quantity}",
                'date': order.created_at,
                'transaction_id': f"ORD-{order.id}"
            })
    
    # Sort transactions by date
    recent_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'user_data': {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        },
        'wallet_data': {
            'current_balance': profile.balance,
            'total_spent': total_spent,
            'total_deposited': total_deposited,
            'recent_transactions': recent_transactions[:10],  # Show last 10 transactions
            'total_orders': len(orders)
        }
    }
    
    return render(request, 'store/wallet.html', context)

@require_POST
@login_required
def deposit_money(request):
    try:
        amount = request.POST.get('amount')
        card_number = request.POST.get('card_number')
        
        # Validate required fields
        if not amount or not card_number:
            return JsonResponse({
                'success': False,
                'error': 'Barcha maydonlarni to\'ldiring'
            })
        
        # Validate amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'To\'lov miqdori 0 dan katta bo\'lishi kerak'
                })
        except:
            return JsonResponse({
                'success': False,
                'error': 'Noto\'g\'ri to\'lov miqdori'
            })
        
        # Validate card number (basic validation)
        card_number = card_number.replace(' ', '').replace('-', '')
        if len(card_number) != 16 or not card_number.isdigit():
            return JsonResponse({
                'success': False,
                'error': 'Noto\'g\'ri karta raqami'
            })
        
        # Format card number for display (1234 5678 9012 3456)
        formatted_card = ' '.join([card_number[i:i+4] for i in range(0, 16, 4)])
        
        # Get user profile first
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Create deposit record
        deposit = Deposit.objects.create(
            user=request.user,
            amount=amount,
            card_number=formatted_card,
            status='completed'  # In real app, this would be 'pending' until payment is confirmed
        )
        
        # Refresh the profile to get updated balance
        profile.refresh_from_db()
        
        return JsonResponse({
            'success': True,
            'message': f'{amount} so\'m muvaffaqiyatli to\'ldirildi!',
            'new_balance': str(profile.balance),
            'deposit_amount': str(amount)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Xatolik yuz berdi: ' + str(e)
        })

def about_us(request):
    # Get user data if logged in
    user_data = {
        'name': 'Foydalanuvchi',
        'email': 'foydalanuvchi@email.com',
        'balance': 0.00,
        'orders_count': 0,
        'bonus_points': 0
    }
    
    if request.user.is_authenticated:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        user_data = {
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'email': user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
    
    context = {
        'user_data': user_data
    }
    
    return render(request, 'store/about_us.html', context)

def clothing_page(request):
    # Get user data if logged in
    user_data = {
        'name': 'Foydalanuvchi',
        'email': 'foydalanuvchi@email.com',
        'balance': 0.00,
        'orders_count': 0,
        'bonus_points': 0
    }
    
    if request.user.is_authenticated:
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        user_data = {
            'name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'email': user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
    
    # Define clothing categories
    clothing_categories = [
        {
            'name': 'BMW Kiyimlari',
            'description': 'BMW brendining rasmiy kiyimlari va aksessuarlari',
            'image': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
            'link': '#'
        },
        {
            'name': 'Mercedes-Benz Kiyimlari',
            'description': 'Mercedes-Benz brendining eksklyuziv kiyimlari',
            'image': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
            'link': '#'
        },
        {
            'name': 'Porsche Kiyimlari',
            'description': 'Porsche brendining premium kiyimlari va aksessuarlari',
            'image': 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop',
            'link': '#'
        }
    ]
    
    context = {
        'user_data': user_data,
        'clothing_categories': clothing_categories
    }
    
    return render(request, 'store/clothing.html', context)

@login_required
def deposit_page(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'user_data': {
            'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
            'balance': profile.balance,
            'orders_count': profile.orders_count,
            'bonus_points': profile.bonus_points,
            'avatar': profile.avatar
        }
    }
    return render(request, 'store/deposit.html', context)

@login_required
def pay_page(request):
    return render(request, 'store/pay.html')
