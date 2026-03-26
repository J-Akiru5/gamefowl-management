# Gamefowl Management System - Setup Instructions

## Prerequisites
- Python 3.10+ installed and working
- Git (optional, for version control)

## Setup Steps

### 1. Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (choose based on your terminal):
# For Git Bash / WSL / Linux:
source venv/Scripts/activate

# For Windows CMD:
venv\Scripts\activate.bat

# For Windows PowerShell (if execution policy allows):
venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy environment template (you said you already did this)
cp .env.example .env

# Edit .env with your Supabase credentials:
# DATABASE_URL=postgresql://user:password@host:port/database
```

### 4. Database Setup
```bash
# Create and run migrations
python manage.py makemigrations
python manage.py migrate

# Seed predefined bloodlines
python manage.py seed_bloodlines
```

### 5. Create Admin User
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

### 7. Access Application
- **Main App**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Analytics Dashboard**: http://127.0.0.1:8000/ (landing page)

---

## Troubleshooting

### Virtual Environment Activation Issues
- **Git Bash**: `source venv/Scripts/activate`
- **CMD**: `venv\Scripts\activate.bat`
- **PowerShell**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first

### Database Connection Issues
- Verify your Supabase credentials in `.env`
- Check that your Supabase project allows connections from your IP
- Ensure the database exists

### Missing Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Static Files Issues (in production)
```bash
python manage.py collectstatic
```

---

## Quick Test Commands

After setup, test these features:

```bash
# Check if all apps are working
python manage.py check

# Test database connection
python manage.py dbshell

# Create a test fowl via shell
python manage.py shell
>>> from apps.fowl.models import Gamefowl, Bloodline
>>> from apps.accounts.models import UserProfile
>>> bloodlines = Bloodline.objects.all()
>>> print(f"Found {bloodlines.count()} bloodlines")
```

---

## Next Development Steps

1. **Test basic CRUD**: Create/edit fowl through admin
2. **Test bloodline calculation**: Create parent fowl with bloodlines, then create offspring
3. **Test fight scheduling**: Schedule and complete fights
4. **Test analytics**: View dashboard charts
5. **Test responsive design**: Check mobile layout
6. **Add sample data**: Use admin to populate with test fowl, fights, etc.

## Features Ready to Use

✅ **User Management**: Login, registration, role-based access
✅ **Fowl Management**: Full CRUD with image uploads
✅ **Bloodline Tracking**: Auto-calculation + manual override
✅ **Lineage Tree**: Sire/dam relationships, sibling detection
✅ **Fight Records**: Scheduling and results tracking
✅ **Analytics Dashboard**: Win/loss charts, breed distribution
✅ **Mobile-Friendly**: Bottom nav, responsive design
✅ **Admin Interface**: Full data management

## Future Enhancements (Post-MVP)

- Pedigree tree visualization
- Advanced analytics (breeding recommendations)
- Fight video uploads
- Export/import functionality
- API endpoints
- Social features (forums, marketplace)