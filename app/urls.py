from django.contrib import admin
from django.urls import path
from app import views
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # Fixed import path

urlpatterns = [

    path('',views.index,name='index'),
    path('login_page',views.login_page,name='login_page'),
    path('logout', views.logout_user, name='logout'), 
    path('admin_dashboard',views.admin_dashboard,name='admin_dashboard'),
    path('company_register', views.company_register, name='company_register'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/update/<int:company_id>/', views.update_company, name='update_company'),
    path('companies/delete/<int:company_id>/', views.delete_company, name='delete_company'),
    path('user_register', views.user_register, name='user_register'),
    path('stock-users', views.stockuser_list, name='stockuser_list'),
    path('stock-users/update/<int:user_id>/', views.update_stockuser, name='update_stockuser'),
    path('stock-users/delete/<int:user_id>/', views.delete_stockuser, name='delete_stockuser'),
    path('request_shares', views.request_share_listing, name='request_shares'),
    path('share_list', views.company_share_list, name='share_list'),
    path('share-requests', views.share_request_list, name='share_request_list'),
    path('share-requests/update/<int:pk>/', views.update_share_status, name='update_share_status'),
    path('available_shares', views.available_shares, name='available_shares'),
    path('buy/<int:listing_id>/', views.buy_share, name='buy_share'),
    path('sell/<int:listing_id>/', views.sell_share, name='sell_share'),
    # ✅ NEW — Blockchain routes
    path('verify-transaction/', views.verify_transaction, name='verify_transaction'),
    path('sell-share-web3/', views.sell_share_web3, name='sell_share_web3'),
    path('portfolio', views.user_portfolio_view, name='user_portfolio'),
    path('marketplace', views.stock_marketplace, name='stock_marketplace'),
    path('admin_index',views.admin_index,name='admin_index'),
    path('wallet/topup/', views.wallet_topup, name='wallet_topup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)