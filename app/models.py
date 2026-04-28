from django.db import models

class Company(models.Model):
    company_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255)  # Raw password storage
    wallet_address = models.CharField(max_length=42, unique=True, null=True, blank=True)
    wallet_private_key = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.company_name
    
class StockUser(models.Model):
    full_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=255) # Store hashed passwords here
    amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    wallet_address = models.CharField(max_length=42, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username
    

class ShareListing(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='listings')
    total_shares = models.PositiveIntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    listing_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    @property
    def total_value(self):
        # Calculates: Total Value = Shares * Price
        return self.total_shares * self.price_per_share

    def __str__(self):
        return f"{self.company.company_name} - {self.total_shares} shares"
    
class UserPortfolio(models.Model):
    user = models.ForeignKey(StockUser, on_delete=models.CASCADE)
    listing = models.ForeignKey(ShareListing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    average_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.listing.company.company_name}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [('buy', 'Buy'), ('sell', 'Sell')]
    user = models.ForeignKey(StockUser, on_delete=models.CASCADE)
    listing = models.ForeignKey(ShareListing, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    price_at_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    tx_hash = models.CharField(max_length=100, null=True, blank=True)

class StockPriceHistory(models.Model):
    listing = models.ForeignKey(ShareListing, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.listing.company.company_name} - ₹{self.price} at {self.timestamp}"