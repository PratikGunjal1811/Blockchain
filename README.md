# 📈 StockFlow — Blockchain-Powered Stock Trading Platform

<p align="center">
  <img src="https://img.shields.io/badge/Django-4.x-green?style=for-the-badge&logo=django" />
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Blockchain-Ethereum-purple?style=for-the-badge&logo=ethereum" />
  <img src="https://img.shields.io/badge/Web3-MetaMask-orange?style=for-the-badge&logo=metamask" />
  <img src="https://img.shields.io/badge/Ganache-Local%20Chain-brown?style=for-the-badge" />
</p>

<p align="center">
  <b>A full-stack stock trading simulation platform with real Ethereum blockchain transactions using MetaMask + Ganache.</b>
</p>

---

## 🖼️ Screenshots

### 🏠 Home Page
![Home](home.png)

### 📊 Stock Marketplace (User Dashboard)
![Marketplace](marketplace.png)

### 🛒 Available Shares & Buy/Sell
![Available Shares](admin_dashboard.png)

### 💼 Portfolio
![Portfolio](portfolio.png)

---

## 🚀 Features

- 🔐 **Multi-role Login** — Admin, Company, and Stock User
- 🏢 **Company Registration** with Ethereum wallet address
- 👤 **User Registration** with Ethereum wallet address
- 📋 **Share Listing** — Companies request shares, Admin approves/rejects
- 💰 **Buy Shares** — User pays ETH via MetaMask to company wallet
- 💸 **Sell Shares** — Company automatically sends ETH back to user wallet
- 📈 **Dynamic Pricing** — Price increases on buy, decreases on sell
- 📊 **Price History Charts** — Real-time stock price tracking
- 💳 **INR Wallet** — Virtual INR balance updated on every trade
- 🔗 **Blockchain TX Hash** — Every transaction recorded on Ethereum
- 📉 **Portfolio Tracker** — P&L, current value, avg buy price
- 🧾 **Transaction History** — Full trade log with blockchain hashes

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.x (Python) |
| Frontend | Bootstrap 5, HTML, CSS, JS |
| Database | SQLite3 |
| Blockchain | Ethereum (Ganache local chain) |
| Web3 Library | web3.py (backend), ethers.js (frontend) |
| Wallet | MetaMask |
| Charts | Chart.js |
| Alerts | SweetAlert2 |

---

## 🔗 Blockchain Flow

```
BUY FLOW:
User clicks Buy
    → MetaMask popup opens
    → User pays ETH to Company wallet
    → TX hash sent to Django backend
    → Backend verifies TX on Ganache
    → DB updated (shares, portfolio, INR wallet)
    → TX hash saved to Transaction record

SELL FLOW:
User clicks Sell
    → Django backend reads Company private key
    → Backend sends ETH from Company → User wallet automatically
    → DB updated (shares, portfolio, INR wallet)
    → TX hash saved to Transaction record
```

---

## 🛠️ Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/ujjwalkatare/stockflow-django.git
cd stockflow-django
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Start Ganache
- Download [Ganache](https://trufflesuite.com/ganache/)
- Start a new workspace on port **7545**
- Note down account addresses and private keys

### 6. Configure MetaMask
- Add custom network: `http://127.0.0.1:7545` — Chain ID: `1337`
- Import a Ganache account using its private key

### 7. Run the server
```bash
python manage.py runserver
```

### 8. Open in browser
```
http://127.0.0.1:8000
```

---

## 👥 Roles & Login

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | `admin` | `admin` | Full system control |
| Company | Register via form | — | List shares, view dashboard |
| User | Register via form | — | Buy/sell shares, portfolio |

---

## 📁 Project Structure

```
StockFlow/
├── app/
│   ├── models.py          # Company, StockUser, ShareListing, Transaction, etc.
│   ├── views.py           # All views including blockchain buy/sell logic
│   ├── urls.py            # URL routing
│   └── admin.py           # Django admin registration
├── templates/
│   ├── available_shares.html    # Buy/Sell with MetaMask
│   ├── stock_marketplace.html   # User dashboard
│   ├── portfolio.html           # Portfolio tracker
│   ├── company_register.html    # Company registration with wallet
│   ├── user_register.html       # User registration with wallet
│   └── ...
├── static/                # CSS, JS, images
├── manage.py
└── requirements.txt
```

---

## 📦 Requirements

```
django
web3
```

Install all:
```bash
pip install django web3
```

---

## 🔐 Environment Notes

- Ganache must be running on `http://127.0.0.1:7545` before starting the server
- Company and User must have **different** Ganache wallet addresses
- MetaMask must be connected to Ganache network (Chain ID: 1337)
- The active MetaMask account must match the user's registered wallet address

---

## 👨‍💻 Author

**Ujjwal Katare**

[![GitHub](https://img.shields.io/badge/GitHub-ujjwalkatare-black?style=flat&logo=github)](https://github.com/ujjwalkatare)

---

## ⭐ Give a Star

If you found this project helpful, please consider giving it a ⭐ on GitHub!
