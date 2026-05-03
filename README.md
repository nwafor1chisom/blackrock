# BLACKROCK — Unified Fintech Platform

One production-grade Django system combining:
- **Public Marketing Site** (ZIP frontend — home, plan, contact, about, faq)
- **Full Fintech Backend** (wallet, ledger, KYC, transactions, OTP, referral)

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run ALL migrations
python manage.py makemigrations users wallet ledger transactions kyc payments referral core
python manage.py migrate

# 3. Seed demo data (admin, plans, payment methods)
python manage.py setup_demo

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Start server
python manage.py runserver
```

---

## 🗺 URL Map

| URL | Description |
|---|---|
| `/` | Smart redirect: guests→home, auth→dashboard |
| `/plan/` | Investment plans — **fully dynamic from DB** |
| `/contact/` | Contact form (AJAX) + WhatsApp support |
| `/about/` | About page |
| `/faq/` | FAQ page |
| `/users/login/` | Login |
| `/users/register/` | Register |
| `/dashboard/` | User financial dashboard |
| `/transactions/deposit/` | Deposit funds |
| `/transactions/withdraw/` | Withdraw funds |
| `/kyc/submit/` | KYC verification |
| `/referral/` | Refer & Earn |
| `/adminpanel/` | Custom financial governance panel |
| `/admin/` | Django admin |

---

## 💰 Investment Plan System

Plans are managed entirely via Django admin:

1. Go to `/admin/core/investmentplan/`
2. Create/edit plans: name, interest%, duration, min/max amount
3. Toggle `is_active` to show/hide on the public plan page
4. `sort_order` controls display order

When authenticated users click **"Invest Now"** on a plan:
- A modal opens showing the plan summary
- Clicking "Proceed to Deposit" routes to `/transactions/deposit/?plan=PlanName`
- The deposit page shows a banner confirming the plan selected
- Admin approves the deposit → ledger credits balance

---

## 📬 Contact Form System

- Form submits via AJAX to `/contact/` (POST)
- Every submission saved to `ContactMessage` model (viewable at `/admin/core/contactmessage/`)
- Admin email notification sent to `CONTACT_ADMIN_EMAIL` setting
- WhatsApp button uses `WHATSAPP_NUMBER` setting (no hardcoding)

To configure:
```python
# blackrock/settings.py
CONTACT_ADMIN_EMAIL = 'your@email.com'
WHATSAPP_NUMBER     = '18625967401'   # international format, no +
```

---

## ⚙️ Key Settings

```python
# Email (for OTP + contact notifications)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = 'smtp.gmail.com'
EMAIL_PORT     = 587
EMAIL_USE_TLS  = True
EMAIL_HOST_USER     = 'your@email.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

OTP_DEBUG_PRINT     = False   # Set True in dev to print OTPs to console

CONTACT_ADMIN_EMAIL = 'supportblackrock@gmail.com'
WHATSAPP_NUMBER     = '18625967401'
```

---

## 🏗 Architecture

```
blackrock/
├── core/           → Public site (home, plan, contact, about, faq)
│   ├── models.py   → InvestmentPlan, ContactMessage, AuditLog
│   ├── views.py    → All public views + AJAX contact handler
│   └── admin.py    → Manage plans & read messages
├── users/          → Auth (register, login, OTP password reset)
├── wallet/         → Per-user ledger-backed wallet
├── ledger/         → Double-entry accounting engine
├── transactions/   → Deposits & withdrawals (admin approval flow)
├── payments/       → Crypto payment methods (admin-managed)
├── kyc/            → Identity verification
├── referral/       → Refer & Earn system
├── adminpanel/     → Custom financial governance dashboard
├── templates/
│   ├── base.html           → App dashboard base (dark gold theme)
│   └── public/
│       ├── base.html       → Public site base (ZIP frontend)
│       ├── home.html       → Landing page (standalone)
│       ├── plan.html       → Investment plans (100% DB-driven)
│       ├── contact.html    → Contact form + WhatsApp
│       ├── about.html      → About page
│       ├── faq.html        → FAQ page
│       ├── blog.html       → Blog (placeholder)
│       └── certification.html → Certification (placeholder)
└── static/
    └── core/
        ├── css/style.css   → ZIP frontend CSS (exact, unmodified)
        ├── js/script.js    → ZIP frontend JS (exact, unmodified)
        └── images/logo.jpg → Platform logo
```
