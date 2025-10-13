# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

XBMC is a Flask web application for viewing and exporting government procurement data from MS SQL Server. The application uses a dual-database architecture:
- **MS SQL Server**: External read-only database containing procurement data (`zakupki` table)
- **SQLite**: Local database for user accounts, news, ideas, and transactions

**Repository**: https://github.com/stiapanreha-dev/xbmc

## Tech Stack

- **Backend**: Flask 2.x with Flask-Login, Flask-SQLAlchemy
- **Database**:
  - SQLite (local data)
  - MS SQL Server via `pyodbc` (external data)
- **Frontend**: Bootstrap 5 (local), Jinja2 templates
- **Payment**: ЮKassa API integration
- **Export**: openpyxl for Excel generation

## Project Structure

```
.
├── app/
│   ├── __init__.py          # Flask app factory, context processors
│   ├── models.py            # SQLAlchemy models (User, Transaction, News, Idea, EmailVerification)
│   ├── mssql.py             # MSSQL connection singleton
│   ├── decorators.py        # Custom decorators (@admin_required)
│   ├── email_service.py     # Email service (SMTP integration)
│   ├── sms_service.py       # SMS service (SMS.ru integration)
│   └── routes/
│       ├── auth.py          # Authentication routes (login, register, verification)
│       ├── main.py          # Main application routes
│       └── payment.py       # Payment processing (ЮKassa integration)
├── templates/               # Jinja2 HTML templates
│   ├── verify_email.html    # Email verification page
│   └── verify_phone.html    # Phone verification page
├── static/                  # CSS, JS, Bootstrap vendor files
├── scripts/                 # Служебные скрипты
│   ├── init_db.py           # Database initialization script
│   └── README.md            # Documentation for scripts
├── tests/                   # Тесты приложения
│   ├── test_email_service.py  # Email service tests
│   ├── test_sms_service.py    # SMS service tests
│   └── README.md            # Documentation for tests
├── config.py                # Configuration class
└── run.py                   # Application entry point
```

## Development Commands

### Initial Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with MSSQL, SMTP, and SMS.ru credentials
python3 scripts/init_db.py
```

### Running the Application
```bash
python3 run.py  # Starts on http://localhost:5000
```

### Database Operations
```bash
# Initialize SQLite database (creates users, news, ideas, verifications tables)
python3 scripts/init_db.py
```

### Testing Services
```bash
# Test email verification service
python3 tests/test_email_service.py

# Test SMS verification service
python3 tests/test_sms_service.py

# Test MSSQL connection
python3 << 'EOF'
from app.mssql import mssql
result = mssql.get_zakupki(limit=1)
print(f"Connected! Total records: {result['total']}")
EOF
```

## Architecture

### Dual Database Design

The application maintains separation between:
1. **External Data (MSSQL)**: Read-only procurement data accessed via `app/mssql.py`
   - Connection managed by `MSSQLConnection` class
   - Methods: `get_zakupki()`, `get_companies()`, `get_rubrics()`, `get_subrubrics()`, `get_cities()`
   - Configured via `MSSQL_*` environment variables
   - **Character encoding**: Database contains mixed encodings:
     - `zakupki.purchase_object` - **nvarchar** (UTF-16 Unicode)
     - `zakupki_specification.product` - **varchar** (cp1251 via Cyrillic_General collation)
     - `db_companies`, `db_rubrics`, `db_subrubrics`, `db_cities` - **varchar** (cp1251 via Cyrillic_General_CI_AS collation)
     - **IMPORTANT**: Leave `MSSQL_CHARSET` empty in `.env` to allow pymssql auto-detect encodings
     - Setting explicit charset breaks one of the encodings
   - **Table schema** (`zakupki`):
     - `date_request` (datetime) - Request date
     - `purchase_object` (nvarchar) - Product/service description
     - `start_cost` (decimal) - Contract price
     - `customer` (nvarchar) - Customer name
     - `email` (text) - Customer email
     - `phone` (text) - Customer phone
     - `address` (text) - Customer address
   - **Table schema** (`db_companies`):
     - `id` (int) - Primary key
     - `company` (varchar) - Company name
     - `id_rubric` (int) - FK to db_rubrics
     - `id_subrubric` (int) - FK to db_subrubrics
     - `id_city` (int) - FK to db_cities
     - `phone` (varchar) - Contact phone
     - `mobile_phone` (varchar) - Mobile phone
     - `Email` (varchar) - Contact email
     - `site` (varchar) - Company website
     - `inn` (varchar) - Tax ID (ИНН)
     - `director` (varchar) - Director name
   - **Reference tables**:
     - `db_rubrics`: id, rubric (varchar) - 30 records
     - `db_subrubrics`: id, id_rubric, subrubric (varchar) - 1,431 records
     - `db_cities`: id, city (varchar) - 1,044 records
   - Total companies: ~5.27 million records

2. **Local Data (SQLite)**: User accounts and application data via SQLAlchemy ORM
   - Models defined in `app/models.py`: User, Transaction, News, Idea, EmailVerification
   - Configured via `DATABASE_URL` environment variable

### User Verification System

The application implements two-factor verification for new users:
1. **Email Verification** (via SMTP):
   - Service: `app/email_service.py`
   - SMTP server: smtp.timeweb.ru (port 465, SSL)
   - 6-digit code sent to user email, valid for 10 minutes
   - Configured via `SMTP_*` environment variables

2. **Phone Verification** (via SMS.ru):
   - Service: `app/sms_service.py`
   - API: SMS.ru REST API
   - 6-digit code sent via SMS, valid for 10 minutes
   - Automatic phone number normalization (adds +7 prefix)
   - Configured via `SMSRU_*` environment variables

**Verification Flow**:
- Register → Email verification → Phone verification → Login enabled
- Both email and phone must be verified before user can login
- Admin users created via `scripts/init_db.py` are auto-verified

**Model**: `EmailVerification` stores codes for both email and phone verification
- `verification_type` field: 'email' or 'phone'
- Codes are single-use and expire after 10 minutes
- Resend functionality invalidates old codes

### Role-Based Access Control

Users have a `role` field (`'user'` or `'admin'`):
- Use `@admin_required` decorator from `app/decorators.py` to protect admin routes
- Check `current_user.is_admin()` in templates to show/hide admin UI elements
- Admin users can manage other users' roles via `/admin/users`

### Payment System

The payment module (`app/routes/payment.py`) includes **demo mode**:
- Detects if ЮKassa credentials are test values (`test-shop-id`)
- In demo mode: immediately credits balance without external API calls
- In production mode: integrates with ЮKassa API for real payments

### Template Context

A context processor in `app/__init__.py` automatically injects:
- `news_count`: Count of published news
- `ideas_count`: Count of all ideas

These are available in all templates for the navbar badges.

### Bootstrap Integration

Bootstrap 5 is included locally in `static/vendor/bootstrap/` to work offline. Do not replace CDN links in templates - local files are intentional.

## Application Routes

### Authentication (`app/routes/auth.py`)
- `GET/POST /auth/login` - User login
- `GET/POST /auth/register` - User registration with email/phone
- `GET/POST /auth/verify_email` - Email verification (6-digit code)
- `GET/POST /auth/verify_phone` - Phone verification (6-digit code)
- `POST /auth/resend_verification` - Resend email verification code
- `POST /auth/resend_phone_verification` - Resend SMS verification code
- `GET /auth/profile` - User profile page
- `GET /auth/logout` - User logout

### Main Application (`app/routes/main.py`)
- `GET /` - Main page with procurement data table (filtered, paginated)
- `GET /export` - Export filtered data to Excel (.xlsx)
- `GET /news` - View published news
- `GET/POST /news/add` - Add news (admin only)
- `GET /ideas` - View all ideas
- `GET/POST /ideas/add` - Submit new idea
- `GET /invite` - Invite page
- `GET /support` - Support page
- `GET /admin/users` - User management (admin only)
- `POST /admin/users/<id>/toggle_admin` - Toggle user admin status

### Payment (`app/routes/payment.py`)
- `POST /payment/create` - Create payment (ЮKassa or demo mode)
- `POST /payment/callback` - Payment callback from ЮKassa
- `GET /payment/success` - Payment success page

## Configuration

All sensitive configuration lives in `.env`:
- `SECRET_KEY`: Flask session secret
- `DATABASE_URL`: SQLite path for local data
- `MSSQL_*`: Connection details for external MSSQL database
- `YUKASSA_*`: Payment gateway credentials
- `SMTP_*`: SMTP server configuration for email verification
  - `SMTP_HOST`: SMTP server hostname (smtp.timeweb.ru)
  - `SMTP_PORT`: SMTP port (465 for SSL)
  - `SMTP_USER`: SMTP username
  - `SMTP_PASSWORD`: SMTP password
  - `FROM_EMAIL`: Sender email address
  - `FROM_NAME`: Sender display name
- `SMSRU_*`: SMS.ru API configuration for phone verification
  - `SMSRU_API_KEY`: SMS.ru API key
  - `SMSRU_FROM_NAME`: Optional sender name (if approved)

## Data Export

The `/export` route generates Excel files using `openpyxl`:
- Exports up to 10,000 records (configurable limit)
- Applies same filters as main view (date range, search text)
- Filename format: `zakupki_YYYYMMDD_HHMMSS.xlsx`
- Columns match MSSQL schema: Date, Product/Service, Price, Customer, Email, Phone, Address

## Common Tasks

### Adding a New Admin-Only Route
```python
from app.decorators import admin_required

@bp.route('/admin/something')
@admin_required
def admin_something():
    # Your code here
```

### Querying MSSQL Data
Always use the singleton `mssql` instance from `app.mssql`:
```python
from app.mssql import mssql

result = mssql.get_zakupki(
    date_from=datetime_obj,
    date_to=datetime_obj,
    search_text="keyword",
    limit=100,
    offset=0
)
# Returns: {'data': [...], 'total': count}
```

### Database Schema Changes
When modifying SQLite models (`app/models.py`):
1. Create a migration script in `scripts/` directory
2. Use `db.engine.begin()` context manager for ALTER statements
3. Wrap in `db.text()` for raw SQL
4. Document the migration in `scripts/README.md`

### Testing Services
When testing email or SMS services:
```python
# Run individual tests
python3 tests/test_email_service.py
python3 tests/test_sms_service.py

# Tests are interactive and will prompt for confirmation before sending
```

## Scripts and Tests Organization

### Scripts Directory (`scripts/`)
Contains utility scripts for database management and migrations:
- `init_db.py`: Initialize database with default admin user
- Place all new migration scripts here
- Update `scripts/README.md` when adding new scripts

### Tests Directory (`tests/`)
Contains test files for application services:
- `test_email_service.py`: Email/SMTP verification tests
- `test_sms_service.py`: SMS/Phone verification tests
- Tests are standalone and can be run directly with Python
- Update `tests/README.md` when adding new tests

**Important**: Always place tests in `tests/` and scripts in `scripts/`. Never create test or utility files in project root.

## Localization and User Messages

### Flask-Login Messages
Authentication messages are localized to Russian in `app/__init__.py`:
```python
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'warning'
```

### Flash Message Categories
Template `templates/base.html` handles multiple flash message categories:
- `message` → converted to Bootstrap `info` alert
- `error` → converted to Bootstrap `danger` alert
- Other categories (success, warning, info, danger) → used directly

This ensures consistent styling across all flash messages.

## Windows Development

When working on Windows, use the Python launcher:
```cmd
py run.py                # Instead of python3 run.py
py scripts\init_db.py    # Instead of python3 scripts/init_db.py
py tests\test_sms.py     # Instead of python3 tests/test_sms.py
```

The `py` command is the standard Python launcher on Windows and handles version selection automatically.

## Documentation Files

- **README.md** - Basic project overview
- **QUICKSTART.md** - Quick deployment guide for Windows users (5-minute setup)
- **INSTALL.md** - Detailed installation instructions with SQL Server setup
- **PRODUCTION_WINDOWS.md** - Production deployment on Windows Server
- **CLAUDE.md** - This file, technical documentation for AI assistance
- **.scripts/EMAIL_ISSUE.md** - SMTP troubleshooting guide (VPN issues, etc.)

## Key Constraints

- **MSSQL is read-only**: Never attempt INSERT/UPDATE/DELETE on `zakupki` table
- **Role field is required**: All User instances must have a `role` value
- **Verification required**: Users must verify both email and phone before login
- **Admin user must exist**: `scripts/init_db.py` ensures an admin user is always created (auto-verified)
- **Default test credentials**: admin/admin123 (see README.md)
- **Verification codes**: Single-use, expire after 10 minutes, stored in `EmailVerification` model

## Git Workflow

### Commit Messages
- **NEVER mention Claude or AI assistance in commit messages**
- Write clear, concise commit messages describing the change
- Focus on **what** changed and **why**, not **how** it was created
- Use conventional format: `type: description` (e.g., `feat: add user export`, `fix: resolve login issue`)

### Example Commit Messages
✅ Good:
- `feat: add Excel export for procurement data`
- `fix: resolve MSSQL connection timeout`
- `refactor: improve payment processing logic`

❌ Bad:
- `Generated with Claude Code`
- `AI-assisted implementation of...`
- `Claude helped me fix...`
