from django.contrib import admin
from .models import Company, StockUser, ShareListing, UserPortfolio, Transaction

admin.site.register(Company)
admin.site.register(StockUser)
admin.site.register(ShareListing)
admin.site.register(UserPortfolio)
admin.site.register(Transaction)
