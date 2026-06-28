from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncDay
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json
import re
from web3 import Web3
from .models import (
    Company,
    StockUser,
    ShareListing,
    UserPortfolio,
    Transaction,
    StockPriceHistory
)

# Connect to Ganache
import os
from django.conf import settings as django_settings

GANACHE_RPC_URL = os.environ.get('GANACHE_RPC_URL', 'http://127.0.0.1:7545')

try:
    web3 = Web3(Web3.HTTPProvider(GANACHE_RPC_URL))
    if not web3.is_connected():
        web3 = None
        print("WARNING: Web3 not connected")
    else:
        print(f"Web3 connected to: {GANACHE_RPC_URL}")
except Exception as e:
    web3 = None
    print(f"WARNING: Web3 connection failed: {e}")
ETH_TO_INR_RATE = Decimal('300000')

def index(request):
    return render(request, 'index.html')


def login_page(request):
    if request.method == "POST":
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        # 1. Check for Hardcoded Admin
        if username_input == "admin" and password_input == "admin":
            messages.success(request, "Welcome back, Admin!")
            return redirect('admin_dashboard')

        # 2. Check Company Table
        # Note: Using .filter().first() to avoid DoesNotExist errors
        company = Company.objects.filter(username=username_input, password=password_input).first()
        if company:
            request.session['company_id'] = company.id  # Store ID in session
            request.session['role'] = 'company'
            messages.success(request, f"Welcome, {company.company_name}!")
            return redirect('admin_index') # This is your company dashboard

        # 3. StockUser Login
        stock_user = StockUser.objects.filter(username=username_input, password=password_input).first()
        if stock_user:
            request.session['user_id'] = stock_user.id
            request.session['role'] = 'user'
            messages.success(request, f"Welcome, {stock_user.full_name}!")
            return redirect('stock_marketplace')

        # 4. If none match
        messages.error(request, "Invalid username or password.")
        return redirect('login_page')

    return render(request, 'login_page.html')


def logout_user(request):
    # Log out Django Admin
    logout(request) 
    
    # Log out Teacher (Clear all session data)
    request.session.flush() 
    
    messages.success(request, "You have been logged out.")
    return redirect('login_page')


def company_register(request):
    if request.method == 'POST':
        name     = request.POST.get('company_name', '').strip()
        reg_no   = request.POST.get('registration_number', '').strip()
        address  = request.POST.get('address', '').strip()
        email    = request.POST.get('email', '').strip()
        contact  = request.POST.get('contact_number', '').strip()
        user     = request.POST.get('username', '').strip()
        pwd      = request.POST.get('password', '').strip()
        wallet   = request.POST.get('wallet_address', '').strip()
        privkey  = request.POST.get('wallet_private_key', '').strip()

        if not all([name, reg_no, address, email, contact, user, pwd, wallet]):
            messages.error(request, "All fields are required.")
            return redirect('company_register')

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messages.error(request, "Invalid email format.")
            return redirect('company_register')

        if not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact number must be exactly 10 digits.")
            return redirect('company_register')

        if Company.objects.filter(username=user).exists():
            messages.error(request, "Username already exists!")
            return redirect('company_register')

        if Company.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('company_register')

        if not re.match(r"^0x[a-fA-F0-9]{40}$", wallet):
            messages.error(request, "Invalid Ethereum wallet address.")
            return redirect('company_register')

        if Company.objects.filter(wallet_address=wallet).exists():
            messages.error(request, "Wallet already registered!")
            return redirect('company_register')

        if len(pwd) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect('company_register')

        Company.objects.create(
            company_name=name,
            registration_number=reg_no,
            address=address,
            email=email,
            contact_number=contact,
            username=user,
            password=pwd,
            wallet_address=wallet,
            wallet_private_key=privkey,
        )

        messages.success(request, "Company registered successfully!")
        return redirect('login_page')

    return render(request, 'company_register.html')

def user_register(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        username  = request.POST.get('username')
        email     = request.POST.get('email')
        phone     = request.POST.get('phone')
        password  = request.POST.get('password')
        amount    = request.POST.get('amount')
        wallet    = request.POST.get('wallet_address', '').strip()

        if StockUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('user_register')

        if not wallet:
            messages.error(request, "Wallet address is required.")
            return redirect('user_register')

        if not re.match(r"^0x[a-fA-F0-9]{40}$", wallet):
            messages.error(request, "Invalid Ethereum wallet address.")
            return redirect('user_register')

        if StockUser.objects.filter(wallet_address=wallet).exists():
            messages.error(request, "Wallet already registered!")
            return redirect('user_register')

        StockUser.objects.create(
            full_name=full_name,
            username=username,
            email=email,
            phone=phone,
            password=password,
            amount=amount,
            wallet_address=wallet,
        )

        messages.success(request, "Registration successful! Please login.")
        return redirect('login_page')

    return render(request, 'user_register.html')

def company_list(request):
    """Main view to display the company table."""
    companies = Company.objects.all()
    return render(request, 'company_list.html', {'companies': companies})

def update_company(request, company_id):
    """AJAX handler for updating company details."""
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        company = get_object_or_404(Company, id=company_id)
        try:
            company.company_name = request.POST.get('company_name')
            company.registration_number = request.POST.get('registration_number')
            company.username = request.POST.get('username')
            company.email = request.POST.get('email')
            company.contact_number = request.POST.get('contact_number')
            company.address = request.POST.get('address')
            
            # Update password only if a new one is provided
            new_pass = request.POST.get('password')
            if new_pass and new_pass.strip():
                company.password = new_pass
                
            company.save()
            return JsonResponse({'status': 'success', 'message': 'Company details updated successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})

def delete_company(request, company_id):
    """AJAX handler for deleting a company."""
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        company = get_object_or_404(Company, id=company_id)
        company.delete()
        return JsonResponse({'status': 'success', 'message': 'Company removed successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})


def stockuser_list(request):
    users = StockUser.objects.all().order_by('-created_at')
    return render(request, 'stockuser_management.html', {'users': users})

def update_stockuser(request, user_id):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = get_object_or_404(StockUser, id=user_id)
        
        try:
            user.full_name = request.POST.get('full_name')
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.phone = request.POST.get('phone')
            
            # Update password only if provided
            new_password = request.POST.get('password')
            if new_password and new_password.strip():
                user.password = make_password(new_password)
            
            user.save()
            return JsonResponse({'status': 'success', 'message': 'User updated successfully!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def delete_stockuser(request, user_id):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user = get_object_or_404(StockUser, id=user_id)
        user.delete()
        return JsonResponse({'status': 'success', 'message': 'User deleted successfully!'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def request_share_listing(request):
    # Ensure only a logged-in company can access this
    company_id = request.session.get('company_id')
    if not company_id:
        messages.error(request, "Please login as a Company first.")
        return redirect('login_page')

    company = get_object_or_404(Company, id=company_id)

    if request.method == "POST":
        shares = request.POST.get('total_shares')
        price = request.POST.get('price_per_share')

        ShareListing.objects.create(
            company=company,
            total_shares=shares,
            price_per_share=price,
            status='pending'
        )
        messages.success(request, "Share listing request submitted and is pending approval.")
        return redirect('admin_index')

    return render(request, 'request_shares.html', {'company': company})

def company_share_list(request):
    # Get company ID from session (set during login)
    company_id = request.session.get('company_id')
    
    if not company_id:
        messages.error(request, "Please login as a company to view listings.")
        return redirect('login_page')

    # Fetch the company object
    company = get_object_or_404(Company, id=company_id)
    
    # Fetch all listings for this specific company
    listings = ShareListing.objects.filter(company=company).order_by('-listing_date')

    context = {
        'company': company,
        'listings': listings
    }
    return render(request, 'company_share_list.html', context)


def share_request_list(request):
    # Fetch all share listings
    listings = ShareListing.objects.all().order_by('-listing_date')
    return render(request, 'share_requests.html', {'listings': listings})

def update_share_status(request, pk):
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        listing = get_object_or_404(ShareListing, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in ['approved', 'rejected']:
            listing.status = new_status
            listing.save()
            return JsonResponse({
                'status': 'success', 
                'message': f'Request has been {new_status} successfully.'
            })
        
        return JsonResponse({'status': 'error', 'message': 'Invalid status.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})


PRICE_IMPACT_FACTOR = Decimal('0.01')
MINIMUM_PRICE = Decimal('1.00')


def available_shares(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_page')

    user = StockUser.objects.get(id=user_id)
    listings = ShareListing.objects.filter(status='approved').select_related('company')
    portfolio = UserPortfolio.objects.filter(user=user)
    history = Transaction.objects.filter(user=user).order_by('-timestamp')

    context = {
        'listings': listings,
        'portfolio': portfolio,
        'history': history,
        'user': user,  # Pass user so wallet balance is visible in template
    }
    return render(request, 'available_shares.html', context)

def process_buy(user, listing, quantity_to_buy):
    quantity_to_buy = Decimal(str(quantity_to_buy))

    with transaction.atomic():
        price_increase = listing.price_per_share * (PRICE_IMPACT_FACTOR * quantity_to_buy)
        old_price = listing.price_per_share

        listing.price_per_share += price_increase
        listing.total_shares    -= int(quantity_to_buy)
        listing.save()

        StockPriceHistory.objects.create(listing=listing, price=listing.price_per_share)

        portfolio, created = UserPortfolio.objects.get_or_create(user=user, listing=listing)
        current_qty = Decimal(str(portfolio.quantity))
        avg_price   = Decimal(str(portfolio.average_price))

        total_cost              = (current_qty * avg_price) + (quantity_to_buy * old_price)
        portfolio.quantity     += int(quantity_to_buy)
        portfolio.average_price = total_cost / Decimal(str(portfolio.quantity))
        portfolio.save()

        # ✅ Deduct INR wallet balance on buy
        buy_cost    = old_price * quantity_to_buy
        user.amount = Decimal(str(user.amount)) - buy_cost
        user.save()

        Transaction.objects.create(
            user=user,
            listing=listing,
            transaction_type='buy',
            quantity=int(quantity_to_buy),
            price_at_transaction=old_price,
        )

    return price_increase

def buy_share(request, listing_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_page')

    listing = get_object_or_404(ShareListing, id=listing_id)
    user    = get_object_or_404(StockUser, id=user_id)
    quantity_to_buy = Decimal(request.POST.get('quantity', 1))

    if listing.total_shares < quantity_to_buy:
        messages.error(request, "Not enough shares available!")
        return redirect('available_shares')

    price_increase = process_buy(user, listing, quantity_to_buy)
    messages.success(request, f"Bought shares. Price rose by ₹{price_increase:.2f}")
    return redirect('available_shares')
def process_sell(user, listing, quantity_to_sell):
    quantity_to_sell = Decimal(str(quantity_to_sell))

    with transaction.atomic():
        portfolio = UserPortfolio.objects.select_for_update().get(
            user=user, listing=listing
        )
        if Decimal(str(portfolio.quantity)) < quantity_to_sell:
            raise ValueError("Not enough shares to sell")

        sell_price     = listing.price_per_share
        price_decrease = listing.price_per_share * (PRICE_IMPACT_FACTOR * quantity_to_sell)

        listing.price_per_share = max(
            listing.price_per_share - price_decrease,
            MINIMUM_PRICE
        )
        listing.total_shares += int(quantity_to_sell)
        listing.save()

        StockPriceHistory.objects.create(listing=listing, price=listing.price_per_share)

        portfolio.quantity -= int(quantity_to_sell)
        if portfolio.quantity == 0:
            portfolio.delete()
        else:
            portfolio.save()

        # ✅ Add INR wallet balance on sell
        sale_proceeds = sell_price * quantity_to_sell
        user.amount   = Decimal(str(user.amount)) + sale_proceeds
        user.save()

        Transaction.objects.create(
            user=user,
            listing=listing,
            transaction_type='sell',
            quantity=int(quantity_to_sell),
            price_at_transaction=sell_price
        )

    return sell_price, price_decrease

def sell_share(request, listing_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_page')

    listing   = get_object_or_404(ShareListing, id=listing_id)
    user      = get_object_or_404(StockUser, id=user_id)
    quantity_to_sell = Decimal(request.POST.get('quantity', 1))

    try:
        sell_price, price_drop = process_sell(user, listing, quantity_to_sell)
        messages.success(request, f"Sold shares at ₹{sell_price}. Price dropped by ₹{price_drop:.2f}")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('available_shares')

@csrf_exempt
def verify_transaction(request):
    if request.method != "POST":
        return JsonResponse({"message": "Invalid request"}, status=400)

    data       = json.loads(request.body)
    tx_hash    = data.get("tx_hash")
    listing_id = data.get("listing_id")
    quantity   = Decimal(str(data.get("quantity")))

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({"message": "User not logged in"}, status=401)

    user    = get_object_or_404(StockUser, id=user_id)
    listing = get_object_or_404(ShareListing, id=listing_id)

    try:
        if not tx_hash or len(tx_hash) < 60:
            return JsonResponse({"message": "Invalid transaction hash"}, status=400)

        if Transaction.objects.filter(tx_hash=tx_hash).exists():
            return JsonResponse({"message": "Transaction already used"}, status=400)

        try:
            tx = web3.eth.get_transaction(tx_hash)
        except Exception:
            return JsonResponse({"message": "Transaction not found on blockchain"}, status=400)

        sender    = tx['from']
        receiver  = tx['to']
        value_eth = Decimal(web3.from_wei(tx['value'], 'ether'))

        company_wallet = listing.company.wallet_address
        if not company_wallet:
            return JsonResponse({"message": "Company wallet not set"}, status=400)

        expected_inr = listing.price_per_share * quantity
        expected_eth = expected_inr / ETH_TO_INR_RATE

        # Verify receiver is company wallet
        if receiver.lower() != company_wallet.lower():
            return JsonResponse({"message": "Wrong receiver wallet"}, status=400)

        # Verify amount sent is enough
        if value_eth + Decimal('0.00001') < expected_eth:
            return JsonResponse({"message": "Insufficient ETH payment"}, status=400)

        # Process the buy in DB
        price_increase = process_buy(user, listing, quantity)

        # Save tx_hash to transaction record
        last_tx = Transaction.objects.filter(
            user=user, listing=listing, transaction_type='buy'
        ).order_by('-id').first()

        if last_tx:
            last_tx.tx_hash = tx_hash
            last_tx.save()

        return JsonResponse({
            "message": f"Purchase successful! Price increased by ₹{price_increase:.2f}"
        })

    except Exception as e:
        return JsonResponse({"message": f"Error: {str(e)}"}, status=500)
    
@csrf_exempt
def sell_share_web3(request):
    if request.method != "POST":
        return JsonResponse({"message": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    listing_id = data.get("listing_id")
    raw_qty    = data.get("quantity")

    if not listing_id or not raw_qty:
        return JsonResponse({"message": "listing_id and quantity required"}, status=400)

    quantity = Decimal(str(raw_qty))
    if quantity <= 0:
        return JsonResponse({"message": "Quantity must be > 0"}, status=400)

    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({"message": "User not logged in"}, status=401)

    user    = get_object_or_404(StockUser, id=user_id)
    listing = get_object_or_404(ShareListing, id=listing_id)

    company_wallet  = listing.company.wallet_address
    company_privkey = listing.company.wallet_private_key

    if not user.wallet_address:
        return JsonResponse({"message": "Your wallet address is not set"}, status=400)
    if not company_wallet:
        return JsonResponse({"message": "Company wallet not configured"}, status=400)
    if not company_privkey:
        return JsonResponse({"message": "Company private key not configured"}, status=400)

    if company_wallet.lower() == user.wallet_address.lower():
        return JsonResponse({"message": "Company and user wallet cannot be the same"}, status=400)

    try:
        portfolio = UserPortfolio.objects.filter(user=user, listing=listing).first()
        if not portfolio or Decimal(portfolio.quantity) < quantity:
            return JsonResponse({"message": "Not enough shares to sell"}, status=400)

        sell_price = listing.price_per_share
        total_inr  = sell_price * quantity
        total_eth  = total_inr / ETH_TO_INR_RATE
        total_wei  = web3.to_wei(float(total_eth), 'ether')

        company_wallet_checksum = web3.to_checksum_address(company_wallet)
        user_wallet_checksum    = web3.to_checksum_address(user.wallet_address)

        if not company_privkey.startswith('0x'):
            company_privkey = '0x' + company_privkey

        balance       = web3.eth.get_balance(company_wallet_checksum)
        gas_price     = int(web3.eth.gas_price * 2)
        gas_estimate  = 21000 * gas_price

        if balance < (total_wei + gas_estimate):
            return JsonResponse({
                "message": f"Company wallet has insufficient ETH. "
                           f"Has: {web3.from_wei(balance, 'ether'):.6f} ETH, "
                           f"Needs: {float(total_eth):.6f} ETH + gas"
            }, status=400)

        # DB update first
        sell_price_final, price_drop = process_sell(user, listing, quantity)

        # Send ETH from company to user
        nonce = web3.eth.get_transaction_count(company_wallet_checksum, 'latest')
        tx_data = {
            'nonce':    nonce,
            'to':       user_wallet_checksum,
            'value':    total_wei,
            'gas':      21000,
            'gasPrice': gas_price,
            'chainId':  web3.eth.chain_id,
        }

        signed_tx   = web3.eth.account.sign_transaction(tx_data, private_key=company_privkey)
        tx_hash_raw = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_hex = tx_hash_raw.hex()

        # Save tx_hash
        last_tx = Transaction.objects.filter(
            user=user, listing=listing, transaction_type='sell'
        ).order_by('-id').first()
        if last_tx:
            last_tx.tx_hash = tx_hash_hex
            last_tx.save()

        return JsonResponse({
            "message": f"Sold {quantity} share(s)! ETH sent: {float(total_eth):.6f}",
            "tx_hash": tx_hash_hex
        })

    except ValueError as e:
        return JsonResponse({"message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"message": f"Server error: {str(e)}"}, status=500)

def wallet_topup(request):
    """Add or remove funds from wallet."""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_page')

    user = get_object_or_404(StockUser, id=user_id)

    if request.method == 'POST':
        action = request.POST.get('action')  # 'add' or 'remove'
        try:
            amount = Decimal(request.POST.get('amount', 0))
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero.")
            elif action == 'add':
                user.amount = Decimal(user.amount) + amount
                user.save()
                messages.success(request, f"₹{amount:.2f} added to your wallet. New balance: ₹{user.amount:.2f}")
            elif action == 'remove':
                if Decimal(user.amount) < amount:
                    messages.error(request, f"Cannot withdraw ₹{amount:.2f}. Insufficient balance.")
                else:
                    user.amount = Decimal(user.amount) - amount
                    user.save()
                    messages.success(request, f"₹{amount:.2f} removed from wallet. New balance: ₹{user.amount:.2f}")
            else:
                messages.error(request, "Invalid action.")
        except Exception:
            messages.error(request, "Invalid amount entered.")

    return redirect('available_shares')


def user_portfolio_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_page')
    
    user = get_object_or_404(StockUser, id=user_id)
    portfolio_items = UserPortfolio.objects.filter(user=user).select_related('listing', 'listing__company')
    
    portfolio_data = []
    total_portfolio_value = Decimal('0.00')
    total_pnl = Decimal('0.00')

    for item in portfolio_items:
        current_price = item.listing.price_per_share
        avg_price = Decimal(item.average_price)
        qty = item.quantity
        
        # Core Calculations
        current_value = qty * current_price
        investment_value = qty * avg_price
        pnl = current_value - investment_value
        
        # Safe Division for Percentage
        pnl_percentage = (pnl / investment_value * 100) if investment_value > 0 else 0
        
        total_portfolio_value += current_value
        total_pnl += pnl

        portfolio_data.append({
            'item': item,
            'current_price': current_price,
            'current_value': current_value,
            'pnl': pnl,
            'abs_pnl': abs(pnl),  # <--- Added this to fix the error
            'pnl_percentage': abs(pnl_percentage), # <--- Absolute % for clean UI
            'is_profit': pnl >= 0
        })

    context = {
        'portfolio_data': portfolio_data,
        'total_portfolio_value': total_portfolio_value,
        'total_pnl': total_pnl,
        'abs_total_pnl': abs(total_pnl), # <--- Added for the header summary
        'overall_profit': total_pnl >= 0
    }
    return render(request, 'portfolio.html', context)

def stock_marketplace(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login_page')
    
    try:
        user = StockUser.objects.get(id=user_id)
    except StockUser.DoesNotExist:
        return redirect('login_page')

    listings = ShareListing.objects.filter(status='approved').select_related('company')
    portfolio_map = {p.listing_id: p for p in UserPortfolio.objects.filter(user=user)}
    
    market_data = []
    for listing in listings:
        user_holding = portfolio_map.get(listing.id)
        holding_qty = user_holding.quantity if user_holding else 0
        avg_price = float(user_holding.average_price) if user_holding else 0
        current_price = float(listing.price_per_share)
        
        pnl = (current_price - avg_price) * holding_qty

        # Get History
        history = Transaction.objects.filter(listing=listing).order_by('-timestamp')[:20]
        # We store prices as floats for JS
        prices = [float(t.price_at_transaction) for t in reversed(history)]
        prices.append(current_price)

        market_data.append({
            'listing': listing,
            'pnl': pnl,
            'abs_pnl': abs(pnl),
            'holding_qty': holding_qty,
            'avg_price': avg_price,
            'price_history_json': json.dumps(prices),
            'company_name': listing.company.company_name,
            'trend': 'up' if len(prices) > 1 and prices[-1] >= prices[-2] else 'down'
        })

    return render(request, 'stock_marketplace.html', {'market_data': market_data})


def admin_index(request):
    company_id = request.session.get('company_id')
    if not company_id:
        return redirect('login_page')

    company = get_object_or_404(Company, id=company_id)

    # Get all listings for this company
    company_listings = ShareListing.objects.filter(company=company)

    # --- Stats Cards ---
    total_listings = company_listings.count()
    total_shares_vol = company_listings.aggregate(Sum('total_shares'))['total_shares__sum'] or 0
    market_cap = sum(item.total_value for item in company_listings)

    # Unique investors who bought this company's shares
    total_investors = Transaction.objects.filter(
        listing__company=company, transaction_type='buy'
    ).values('user').distinct().count()

    # --- Recent Listings ---
    recent_listings = company_listings.select_related('company').order_by('-listing_date')[:5]

    # --- Line Chart: Monthly transaction count for this company ---
    transaction_data = (
        Transaction.objects.filter(listing__company=company)
        .annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months = [d['month'].strftime("%b %Y") for d in transaction_data]
    transaction_counts = [d['count'] for d in transaction_data]

    # --- Price History Charts per listing ---
    listings_chart_data = []
    for listing in company_listings:
        history = StockPriceHistory.objects.filter(listing=listing).order_by('timestamp')
        if history.exists():
            listings_chart_data.append({
                'id': listing.id,
                'company_name': listing.company.company_name,
                'labels': [h.timestamp.strftime("%d %b %H:%M") for h in history],
                'prices': [float(h.price) for h in history],
                'current_price': float(listing.price_per_share),
                'total_shares': listing.total_shares,
                'status': listing.status,
            })

    # --- Buy/Sell Volume per listing (bar chart) ---
    buy_sell_data = []
    for listing in company_listings:
        buys = Transaction.objects.filter(listing=listing, transaction_type='buy').aggregate(total=Sum('quantity'))['total'] or 0
        sells = Transaction.objects.filter(listing=listing, transaction_type='sell').aggregate(total=Sum('quantity'))['total'] or 0
        buy_sell_data.append({
            'name': listing.company.company_name,
            'buys': buys,
            'sells': sells,
        })

    context = {
        'company': company,
        'total_listings': total_listings,
        'total_investors': total_investors,
        'total_shares_vol': total_shares_vol,
        'market_cap': market_cap,
        'recent_listings': recent_listings,
        'months': json.dumps(months),
        'transaction_counts': json.dumps(transaction_counts),
        'listings_chart_data': json.dumps(listings_chart_data),
        'buy_sell_data': json.dumps(buy_sell_data),
    }
    return render(request, 'admin_index.html', context)

def admin_dashboard(request):
    # --- Stats Cards ---
    total_companies = Company.objects.count()
    total_users = StockUser.objects.count()
    total_shares_listed = ShareListing.objects.filter(status='approved').count()
    total_transactions = Transaction.objects.count()
    recent_transactions = Transaction.objects.select_related('user', 'listing__company').order_by('-timestamp')[:5]

    # --- Monthly Transaction Line Chart (all system-wide) ---
    transaction_data = (
        Transaction.objects.annotate(month=TruncMonth('timestamp'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months = [d['month'].strftime("%b %Y") for d in transaction_data]
    transaction_counts = [d['count'] for d in transaction_data]

    # --- Buy vs Sell Volume per Company ---
    approved_listings = ShareListing.objects.filter(status='approved').select_related('company')
    buy_sell_data = []
    for listing in approved_listings:
        buys = Transaction.objects.filter(listing=listing, transaction_type='buy').aggregate(total=Sum('quantity'))['total'] or 0
        sells = Transaction.objects.filter(listing=listing, transaction_type='sell').aggregate(total=Sum('quantity'))['total'] or 0
        if buys > 0 or sells > 0:
            buy_sell_data.append({
                'name': listing.company.company_name,
                'buys': buys,
                'sells': sells,
            })

    # --- Per-Listing Price History Charts (all approved listings) ---
    listings_chart_data = []
    for listing in approved_listings:
        history = StockPriceHistory.objects.filter(listing=listing).order_by('timestamp')
        if history.exists():
            listings_chart_data.append({
                'id': listing.id,
                'company_name': listing.company.company_name,
                'labels': [h.timestamp.strftime("%d %b %H:%M") for h in history],
                'prices': [float(h.price) for h in history],
                'current_price': float(listing.price_per_share),
                'total_shares': listing.total_shares,
                'status': listing.status,
            })

    context = {
        'total_companies': total_companies,
        'total_users': total_users,
        'total_shares_listed': total_shares_listed,
        'total_transactions': total_transactions,
        'recent_transactions': recent_transactions,
        'months': json.dumps(months),
        'transaction_counts': json.dumps(transaction_counts),
        'buy_sell_data': json.dumps(buy_sell_data),
        'listings_chart_data': json.dumps(listings_chart_data),
    }
    return render(request, 'admin_dashboard.html', context)
