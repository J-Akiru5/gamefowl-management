"""
Management command to create a dedicated admin account.
Run with: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create a dedicated admin account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Admin username (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@gamefowl-system.com',
            help='Admin email (default: admin@gamefowl-system.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Admin2024!',
            help='Admin password (default: Admin2024!)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists.')
            )
            user = User.objects.get(username=username)
        else:
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created superuser: {username}')
            )

        # Ensure UserProfile exists and is set to admin
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': UserProfile.Role.ADMIN,
                'farm_name': 'System Administration',
                'contact_number': '+1-555-ADMIN',
                'address': 'System Generated Account',
            }
        )

        if not created:
            # Update existing profile to admin role
            profile.role = UserProfile.Role.ADMIN
            profile.farm_name = 'System Administration'
            profile.contact_number = '+1-555-ADMIN'
            profile.address = 'System Generated Account'
            profile.save()
            self.stdout.write(f'Updated profile for: {username}')
        else:
            self.stdout.write(f'Created profile for: {username}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('DEDICATED ADMIN ACCOUNT CREATED'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Role: Administrator')
        self.stdout.write(f'Farm: System Administration')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Login at: http://127.0.0.1:8000/admin/'))
        self.stdout.write(self.style.SUCCESS('Or main app: http://127.0.0.1:8000/'))
        self.stdout.write(self.style.SUCCESS('=' * 50))