# ========================================
# FINAL SETUP STEPS - Run These Manually
# ========================================

# 1. Create Superuser (Interactive - Run this in your terminal)
venv\Scripts\python.exe manage.py createsuperuser
# Enter: username, email, password when prompted

# 2. Start Development Server
venv\Scripts\python.exe manage.py runserver

# 3. Visit Your Application
# Main App: http://127.0.0.1:8000/
# Admin Panel: http://127.0.0.1:8000/admin/

# ========================================
# WHAT'S READY TO TEST
# ========================================

✅ Database connected and migrated
✅ 15 predefined bloodlines seeded:
   - Hatch, Kelso, Sweater, Roundhead, Albany
   - Grey, Claret, Butcher, Radio, Asil
   - Lemon, Whitehackle, Brown Red, Mug, Blueface

✅ All Django apps configured:
   - accounts (User profiles & roles)
   - fowl (Gamefowl & bloodlines)
   - fights (Scheduling & records)
   - analytics (Dashboard charts)

✅ Glassmorphic UI with Tailwind CSS
✅ Mobile-responsive design
✅ Role-based access control

# ========================================
# TESTING CHECKLIST
# ========================================

After creating superuser and starting server:

1. Login to admin (http://127.0.0.1:8000/admin/)
2. Create a UserProfile for your superuser
3. Add some test gamefowl with bloodlines
4. Test lineage relationships (sire/dam)
5. Schedule and complete fights
6. View analytics dashboard
7. Test mobile responsive layout

# ========================================
# TROUBLESHOOTING
# ========================================

If you encounter any issues:
- Check .env file has correct Supabase credentials
- Ensure virtual environment is activated
- Check Python version: venv\Scripts\python.exe --version
- View Django logs for specific errors