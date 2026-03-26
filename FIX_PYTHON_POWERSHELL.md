# ========================================
# PYTHON INSTALLATION FIX - PowerShell Commands
# ========================================

# 1. UNINSTALL BROKEN PYTHON
# Open PowerShell as Administrator and run:

# Check what Python versions are installed
Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*Python*"} | Select-Object Name, Version

# Alternative: Use Windows Settings
# Settings > Apps > Search "Python" > Uninstall all Python entries

# 2. CLEAN INSTALLATION VIA WINGET (Recommended)
# Install Python 3.11 via Windows Package Manager:
winget install Python.Python.3.11

# 3. ALTERNATIVE: Download from python.org
# Go to: https://www.python.org/downloads/windows/
# Download "Python 3.11.x - Windows installer (64-bit)"
# ✅ CHECK "Add Python to PATH"
# ✅ CHECK "Install for all users"

# 4. VERIFY INSTALLATION
# Close and reopen PowerShell, then test:
python --version
pip --version

# Should show: Python 3.11.x and pip version

# ========================================
# DJANGO PROJECT SETUP (After Python Fix)
# ========================================

# Navigate to project directory
cd "S:\Dev\DJANGO\Gamefowl Management System"

# Create virtual environment
python -m venv venv

# Activate virtual environment (PowerShell)
venv\Scripts\Activate.ps1

# If you get execution policy error, run this first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Seed bloodlines
python manage.py seed_bloodlines

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Visit: http://127.0.0.1:8000/