from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('place-order/', views.place_order, name='place_order'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('wallet/', views.wallet, name='wallet'),
    path('deposit/', views.deposit_money, name='deposit_money'),
    path('about/', views.about_us, name='about_us'),
    path('clothing/', views.clothing_page, name='clothing'),
    path('deposit-page/', views.deposit_page, name='deposit_page'),
    path('pay/', views.pay_page, name='pay_page'),
] 