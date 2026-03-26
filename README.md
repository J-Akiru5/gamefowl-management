# Gamefowl Management System

A Django-based application for managing gamefowl, including bloodline tracking, fight records, and analytics.

## Prerequisites

Before you begin, ensure you have the following installed on your local machine:
- **Python 3.10+** (verified working)
- **Git**
- **PostgreSQL** (or access to a Supabase PostgreSQL database)

## Local Setup Instructions

Follow these simple steps from your terminal or command prompt to get the development environment running on your computer.

### 1. Clone the Repository

Download the project source code to your machine:

```bash
git clone https://github.com/J-Akiru5/gamefowl-management.git
cd "gamefowl-management"
```
*(If the repository is cloned into a slightly different folder name, simply `cd` into that directory).*

### 2. Create and Activate a Virtual Environment

Isolate project dependencies using a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (CMD):
venv\Scripts\activate.bat

# Activate on Windows (PowerShell):
venv\Scripts\Activate.ps1

# Activate on macOS/Linux/Git Bash:
source venv/Scripts/activate
# (or source venv/bin/activate on native Linux setups)
```

### 3. Install Requirements

Install all necessary Python packages and dependencies needed for the app:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The project requires environment variables to connect to the database.

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   *(On Windows CMD use: `copy .env.example .env`)*

2. Open the `.env` file and update it with your actual database credentials:
   ```ini
   # Example .env configuration
   DATABASE_URL=postgresql://user:password@host:port/database
   SECRET_KEY=your_development_secret_key
   DEBUG=True
   ```

### 5. Setup the Database

Initialize your database schema and apply migrations:

```bash
# Apply database migrations
python manage.py migrate

# Seed predefined bloodlines to base your fowls on
python manage.py seed_bloodlines
```

### 6. Create an Admin User

Create a superuser account to access the secure Django admin panel for managing the system data:

```bash
python manage.py createsuperuser
```
Follow the prompts to configure your username, email, and password. You will use these credentials to log in.

### 7. Run the Application Locally

Start the Django development server:

```bash
python manage.py runserver
```

### 8. Access the Application

Once the server is running, open your web browser and visit the following addresses:
- **Main App & Analytics Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Panel**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Troubleshooting

- **Virtual Environment Execution Error (Windows PowerShell)**: If PowerShell blocks the activation script, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first.
- **Database Connection Issues**: Verify your `DATABASE_URL` in the `.env` file. If you are using a cloud database like Supabase, make sure your current IP address is whitelisted or you are using the correct connection pooler.
- **Missing Dependencies**: Verify your virtual environment is fully activated before running pip commands. If issues persist, try running `python -m pip install --upgrade pip` and then reinstall the requirements.
