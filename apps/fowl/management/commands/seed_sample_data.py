"""
Management command to seed comprehensive sample data for the Gamefowl Management System.
Creates admin user "Ms.Hze", realistic gamefowl with lineage, and fight records.

Usage:
    python manage.py seed_sample_data
    python manage.py seed_sample_data --user-only
    python manage.py seed_sample_data --clear-all
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction, models

# Import models
from apps.accounts.models import UserProfile
from apps.fowl.models import Gamefowl, Bloodline, FowlBloodline
from apps.fights.models import Fight


class Command(BaseCommand):
    help = 'Seed comprehensive sample data including admin user, gamefowl, and fights'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all sample data before seeding',
        )
        parser.add_argument(
            '--clear-users',
            action='store_true',
            help='Clear only sample users',
        )
        parser.add_argument(
            '--clear-fowl',
            action='store_true',
            help='Clear only sample gamefowl data',
        )
        parser.add_argument(
            '--clear-fights',
            action='store_true',
            help='Clear only sample fight data',
        )
        parser.add_argument(
            '--user-only',
            action='store_true',
            help='Create only the admin user (Ms.Hze)',
        )
        parser.add_argument(
            '--minimal',
            action='store_true',
            help='Create minimal dataset for quick testing',
        )

    def handle(self, *args, **options):
        # Clear data if requested
        if options['clear_all']:
            self._clear_all_sample_data()
        elif options['clear_users']:
            self._clear_sample_users()
        elif options['clear_fowl']:
            self._clear_sample_fowl()
        elif options['clear_fights']:
            self._clear_sample_fights()

        # Create sample data
        with transaction.atomic():
            try:
                # Phase 1: Create Admin User
                admin_user, admin_profile = self._create_admin_user()

                if options['user_only']:
                    self._display_completion_message(
                        admin_user, admin_profile,
                        fowl_count=0, fight_count=0, bloodline_records=0
                    )
                    return

                # Phase 2: Create Foundation Gamefowl (Generation 0)
                foundation_birds = self._create_foundation_gamefowl(admin_profile)

                # Phase 3: Create F1 Generation
                f1_birds = self._create_f1_generation(foundation_birds, admin_profile)

                # Phase 4: Create F2 Generation (only if not minimal)
                f2_birds = []
                if not options['minimal']:
                    f2_birds = self._create_f2_generation(f1_birds, admin_profile)

                # Phase 5: Create Fight Records
                fight_count = self._create_fight_records(
                    foundation_birds + f1_birds + f2_birds,
                    minimal=options['minimal']
                )

                # Phase 6: Validation
                self._validate_data_integrity()

                # Calculate totals
                total_fowl = len(foundation_birds) + len(f1_birds) + len(f2_birds)
                total_bloodline_records = FowlBloodline.objects.filter(
                    fowl__owner=admin_profile
                ).count()

                # Display completion message
                self._display_completion_message(
                    admin_user, admin_profile,
                    fowl_count=total_fowl,
                    fight_count=fight_count,
                    bloodline_records=total_bloodline_records
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error during seeding: {str(e)}')
                )
                raise CommandError(f'Seeding failed: {str(e)}')

    def _clear_all_sample_data(self):
        """Clear all sample data."""
        self.stdout.write(self.style.WARNING('Clearing all sample data...'))

        # Clear fights
        fight_count = Fight.objects.filter(fowl__owner__user__username='ms.hze').count()
        Fight.objects.filter(fowl__owner__user__username='ms.hze').delete()

        # Clear fowl (will cascade to bloodline percentages)
        fowl_count = Gamefowl.objects.filter(owner__user__username='ms.hze').count()
        Gamefowl.objects.filter(owner__user__username='ms.hze').delete()

        # Clear user
        user_count = 0
        try:
            user = User.objects.get(username='ms.hze')
            user.delete()
            user_count = 1
        except User.DoesNotExist:
            pass

        self.stdout.write(
            self.style.SUCCESS(
                f'Cleared: {user_count} user, {fowl_count} fowl, {fight_count} fights'
            )
        )

    def _clear_sample_users(self):
        """Clear only sample users."""
        try:
            user = User.objects.get(username='ms.hze')
            user.delete()
            self.stdout.write(self.style.SUCCESS('Cleared sample user: ms.hze'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('Sample user ms.hze not found'))

    def _clear_sample_fowl(self):
        """Clear only sample gamefowl."""
        fowl_count = Gamefowl.objects.filter(owner__user__username='ms.hze').count()
        Gamefowl.objects.filter(owner__user__username='ms.hze').delete()
        self.stdout.write(self.style.SUCCESS(f'Cleared {fowl_count} sample fowl'))

    def _clear_sample_fights(self):
        """Clear only sample fights."""
        fight_count = Fight.objects.filter(fowl__owner__user__username='ms.hze').count()
        Fight.objects.filter(fowl__owner__user__username='ms.hze').delete()
        self.stdout.write(self.style.SUCCESS(f'Cleared {fight_count} sample fights'))

    def _create_admin_user(self):
        """Create the admin user Ms.Hze."""
        user, created = User.objects.update_or_create(
            username='ms.hze',
            defaults={
                'email': 'admin@heritage-bloodlines.com',
                'first_name': 'Ms.',
                'last_name': 'Hze',
                'is_staff': True,
                'is_superuser': True,
            }
        )

        if created or not user.check_password('HeritageFarm2024!'):
            user.set_password('HeritageFarm2024!')
            user.save()

        profile, profile_created = UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'role': UserProfile.Role.ADMIN,
                'farm_name': 'Heritage Bloodlines Farm',
                'contact_number': '+1-555-HERITAGE',
                'address': '123 Derby Lane, Gamefowl Valley, TX 75001',
            }
        )

        status = "Created" if created else "Updated"
        self.stdout.write(f'  {status}: Admin user ms.hze')

        return user, profile

    def _create_foundation_gamefowl(self, owner):
        """Create foundation birds (Generation 0) with pure bloodlines."""
        self.stdout.write('Creating foundation birds (Generation 0)...')

        # Get bloodlines for foundation birds
        bloodlines = {
            'Hatch': Bloodline.objects.get(name='Hatch'),
            'Kelso': Bloodline.objects.get(name='Kelso'),
            'Sweater': Bloodline.objects.get(name='Sweater'),
            'Roundhead': Bloodline.objects.get(name='Roundhead'),
            'Grey': Bloodline.objects.get(name='Grey'),
            'Claret': Bloodline.objects.get(name='Claret'),
            'Albany': Bloodline.objects.get(name='Albany'),
            'Whitehackle': Bloodline.objects.get(name='Whitehackle'),
        }

        # Foundation bird definitions
        foundation_data = [
            # Males (Roosters)
            {
                'name': 'Thunder Strike',
                'gender': 'male',
                'bloodline': 'Hatch',
                'wing_band': 'HF001',
                'weight': 2.3,
                'leg_color': 'Yellow',
                'plumage_color': 'Dark Red',
                'comb_type': 'Straight',
            },
            {
                'name': 'Lightning Kelso',
                'gender': 'male',
                'bloodline': 'Kelso',
                'wing_band': 'HF002',
                'weight': 2.1,
                'leg_color': 'Green',
                'plumage_color': 'Red',
                'comb_type': 'Pea',
            },
            {
                'name': 'Steel Sweater',
                'gender': 'male',
                'bloodline': 'Sweater',
                'wing_band': 'HF003',
                'weight': 2.4,
                'leg_color': 'White',
                'plumage_color': 'Brown Red',
                'comb_type': 'Straight',
            },
            {
                'name': 'Red Roundhead',
                'gender': 'male',
                'bloodline': 'Roundhead',
                'wing_band': 'HF004',
                'weight': 2.2,
                'leg_color': 'Slate',
                'plumage_color': 'Dark Red',
                'comb_type': 'Rose',
            },
            # Females (Hens)
            {
                'name': 'Diamond Grey',
                'gender': 'female',
                'bloodline': 'Grey',
                'wing_band': 'HF005',
                'weight': 1.6,
                'leg_color': 'Yellow',
                'plumage_color': 'Grey',
                'comb_type': 'Straight',
            },
            {
                'name': 'Ruby Claret',
                'gender': 'female',
                'bloodline': 'Claret',
                'wing_band': 'HF006',
                'weight': 1.5,
                'leg_color': 'Willow',
                'plumage_color': 'Claret',
                'comb_type': 'Pea',
            },
            {
                'name': 'Golden Albany',
                'gender': 'female',
                'bloodline': 'Albany',
                'wing_band': 'HF007',
                'weight': 1.7,
                'leg_color': 'Green',
                'plumage_color': 'Wheaten',
                'comb_type': 'Straight',
            },
            {
                'name': 'Silver Whitehackle',
                'gender': 'female',
                'bloodline': 'Whitehackle',
                'wing_band': 'HF008',
                'weight': 1.4,
                'leg_color': 'White',
                'plumage_color': 'Silver',
                'comb_type': 'Rose',
            },
        ]

        foundation_birds = []
        birth_base = timezone.now().date() - timedelta(days=1200)  # About 3+ years old

        for i, bird_data in enumerate(foundation_data):
            # Create gamefowl
            fowl, created = Gamefowl.objects.update_or_create(
                wing_band=bird_data['wing_band'],
                defaults={
                    'name': bird_data['name'],
                    'gender': bird_data['gender'],
                    'owner': owner,
                    'breed': f"Foundation {bird_data['bloodline']}",
                    'status': 'active',
                    'date_of_birth': birth_base + timedelta(days=i*10),
                    'weight': Decimal(str(bird_data['weight'])),
                    'leg_color': bird_data['leg_color'],
                    'plumage_color': bird_data['plumage_color'],
                    'comb_type': bird_data['comb_type'],
                    'notes': f'Foundation breeding bird with pure {bird_data["bloodline"]} bloodline.',
                }
            )

            # Create bloodline percentage (100% pure)
            FowlBloodline.objects.update_or_create(
                fowl=fowl,
                bloodline=bloodlines[bird_data['bloodline']],
                defaults={
                    'percentage': Decimal('100.00'),
                    'is_manual_override': True,  # Foundation birds are manually set
                }
            )

            foundation_birds.append(fowl)
            status = "Created" if created else "Updated"
            self.stdout.write(f'  {status}: {fowl.name} (100% {bird_data["bloodline"]})')

        return foundation_birds

    def _create_f1_generation(self, foundation_birds, owner):
        """Create F1 generation with 50/50 bloodline inheritance."""
        self.stdout.write('Creating F1 generation crosses...')

        # Separate males and females from foundation
        males = [b for b in foundation_birds if b.gender == 'male']
        females = [b for b in foundation_birds if b.gender == 'female']

        f1_birds = []
        birth_base = timezone.now().date() - timedelta(days=400)  # About 1+ year old

        # F1 Cross combinations
        crosses = [
            # (sire, dam, offspring_name, offspring_gender, wing_band)
            (males[0], females[0], 'Thunder Grey', 'male', 'F1001'),     # Hatch x Grey
            (males[0], females[0], 'Storm Grey', 'female', 'F1002'),     # Hatch x Grey
            (males[1], females[1], 'Lightning Ruby', 'male', 'F1003'),   # Kelso x Claret
            (males[1], females[1], 'Ruby Lightning', 'female', 'F1004'), # Kelso x Claret
            (males[2], females[2], 'Steel Albany', 'male', 'F1005'),     # Sweater x Albany
            (males[2], females[2], 'Golden Steel', 'female', 'F1006'),   # Sweater x Albany
            (males[3], females[3], 'Silver Round', 'male', 'F1007'),     # Roundhead x Whitehackle
            (males[3], females[3], 'White Thunder', 'female', 'F1008'),  # Roundhead x Whitehackle
            (males[0], females[2], 'Hatch Albany', 'male', 'F1009'),     # Hatch x Albany
            (males[1], females[3], 'Kelso White', 'female', 'F1010'),    # Kelso x Whitehackle
            (males[2], females[0], 'Sweater Grey', 'male', 'F1011'),     # Sweater x Grey
            (males[3], females[1], 'Round Claret', 'female', 'F1012'),   # Roundhead x Claret
        ]

        for i, (sire, dam, name, gender, wing_band) in enumerate(crosses):
            # Create F1 fowl
            weight = random.uniform(1.8, 2.3) if gender == 'male' else random.uniform(1.3, 1.7)

            fowl, created = Gamefowl.objects.update_or_create(
                wing_band=wing_band,
                defaults={
                    'name': name,
                    'gender': gender,
                    'owner': owner,
                    'breed': 'F1 Cross',
                    'status': 'active',
                    'sire': sire,
                    'dam': dam,
                    'date_of_birth': birth_base + timedelta(days=i*15),
                    'weight': Decimal(str(round(weight, 2))),
                    'leg_color': random.choice(['Yellow', 'Green', 'White', 'Slate']),
                    'plumage_color': random.choice(['Red', 'Dark Red', 'Brown Red']),
                    'comb_type': random.choice(['Straight', 'Pea']),
                    'notes': f'F1 cross between {sire.name} and {dam.name}.',
                }
            )

            # Create 50/50 bloodline split from parents
            self._create_f1_bloodlines(fowl, sire, dam)

            f1_birds.append(fowl)
            status = "Created" if created else "Updated"

            # Get bloodline info for display
            sire_bloodline = sire.bloodline_percentages.first().bloodline.name
            dam_bloodline = dam.bloodline_percentages.first().bloodline.name
            self.stdout.write(f'  {status}: {fowl.name} (50% {sire_bloodline}, 50% {dam_bloodline})')

        return f1_birds

    def _create_f1_bloodlines(self, fowl, sire, dam):
        """Create 50/50 bloodline inheritance for F1 fowl."""
        # Get sire bloodlines (should be 100% single bloodline)
        sire_bloodlines = sire.bloodline_percentages.all()
        dam_bloodlines = dam.bloodline_percentages.all()

        # Clear existing bloodlines
        fowl.bloodline_percentages.all().delete()

        # Add 50% from sire
        for sire_bl in sire_bloodlines:
            percentage = sire_bl.percentage * Decimal('0.5')
            FowlBloodline.objects.create(
                fowl=fowl,
                bloodline=sire_bl.bloodline,
                percentage=percentage,
                is_manual_override=False,
            )

        # Add 50% from dam
        for dam_bl in dam_bloodlines:
            # Check if this bloodline already exists (same bloodline from both parents)
            existing = fowl.bloodline_percentages.filter(bloodline=dam_bl.bloodline).first()
            if existing:
                # Add to existing percentage
                existing.percentage += dam_bl.percentage * Decimal('0.5')
                existing.save()
            else:
                # Create new bloodline entry
                percentage = dam_bl.percentage * Decimal('0.5')
                FowlBloodline.objects.create(
                    fowl=fowl,
                    bloodline=dam_bl.bloodline,
                    percentage=percentage,
                    is_manual_override=False,
                )

    def _create_f2_generation(self, f1_birds, owner):
        """Create F2 generation with complex bloodline mixes."""
        self.stdout.write('Creating F2 generation (complex bloodlines)...')

        # Separate F1 males and females
        f1_males = [b for b in f1_birds if b.gender == 'male']
        f1_females = [b for b in f1_birds if b.gender == 'female']

        f2_birds = []
        birth_base = timezone.now().date() - timedelta(days=180)  # About 6 months old

        # F2 crosses (using some F1 birds as parents)
        f2_crosses = [
            (f1_males[0], f1_females[1], 'Complex Thunder', 'male', 'F2001'),
            (f1_males[1], f1_females[0], 'Multi Ruby', 'female', 'F2002'),
            (f1_males[2], f1_females[3], 'Steel Lightning', 'male', 'F2003'),
            (f1_males[3], f1_females[2], 'Golden Storm', 'female', 'F2004'),
            (f1_males[0], f1_females[3], 'Thunder White', 'male', 'F2005'),
            (f1_males[2], f1_females[1], 'Steel Ruby', 'female', 'F2006'),
            (f1_males[1], f1_females[2], 'Lightning Gold', 'male', 'F2007'),
            (f1_males[3], f1_females[0], 'Silver Grey', 'female', 'F2008'),
        ]

        for i, (sire, dam, name, gender, wing_band) in enumerate(f2_crosses):
            # Create F2 fowl
            weight = random.uniform(1.7, 2.2) if gender == 'male' else random.uniform(1.2, 1.6)

            fowl, created = Gamefowl.objects.update_or_create(
                wing_band=wing_band,
                defaults={
                    'name': name,
                    'gender': gender,
                    'owner': owner,
                    'breed': 'F2 Multi-Line',
                    'status': 'active',
                    'sire': sire,
                    'dam': dam,
                    'date_of_birth': birth_base + timedelta(days=i*20),
                    'weight': Decimal(str(round(weight, 2))),
                    'leg_color': random.choice(['Yellow', 'Green', 'White', 'Slate', 'Willow']),
                    'plumage_color': random.choice(['Red', 'Dark Red', 'Brown Red', 'Wheaten']),
                    'comb_type': random.choice(['Straight', 'Pea', 'Rose']),
                    'notes': f'F2 multi-bloodline cross from {sire.name} x {dam.name}.',
                }
            )

            # Create complex bloodline inheritance
            self._create_f2_bloodlines(fowl, sire, dam)

            f2_birds.append(fowl)
            status = "Created" if created else "Updated"

            # Get complex bloodline display
            bloodlines_display = self._get_bloodline_display(fowl)
            self.stdout.write(f'  {status}: {fowl.name} ({bloodlines_display})')

        return f2_birds

    def _create_f2_bloodlines(self, fowl, sire, dam):
        """Create complex bloodline inheritance for F2 fowl."""
        from collections import defaultdict

        # Clear existing bloodlines
        fowl.bloodline_percentages.all().delete()

        # Combine bloodlines from both parents (25% from each grandparent line)
        bloodline_totals = defaultdict(Decimal)

        # Add 50% from sire's bloodlines
        for sire_bl in sire.bloodline_percentages.all():
            percentage = sire_bl.percentage * Decimal('0.5')
            bloodline_totals[sire_bl.bloodline_id] += percentage

        # Add 50% from dam's bloodlines
        for dam_bl in dam.bloodline_percentages.all():
            percentage = dam_bl.percentage * Decimal('0.5')
            bloodline_totals[dam_bl.bloodline_id] += percentage

        # Create bloodline records
        for bloodline_id, percentage in bloodline_totals.items():
            if percentage > 0:
                FowlBloodline.objects.create(
                    fowl=fowl,
                    bloodline_id=bloodline_id,
                    percentage=percentage,
                    is_manual_override=False,
                )

    def _get_bloodline_display(self, fowl):
        """Get a display string for fowl's bloodlines."""
        bloodlines = fowl.bloodline_percentages.order_by('-percentage')[:3]
        parts = []
        for bl in bloodlines:
            parts.append(f'{bl.percentage}% {bl.bloodline.name}')
        return ', '.join(parts)

    def _create_fight_records(self, fowls, minimal=False):
        """Create realistic fight records."""
        self.stdout.write('Creating fight records...')

        # Filter fighting age birds (males 8+ months, active status)
        fighting_birds = [
            f for f in fowls
            if f.gender == 'male' and f.status == 'active'
            and f.date_of_birth and
            (timezone.now().date() - f.date_of_birth).days >= 240  # 8+ months
        ]

        if not fighting_birds:
            self.stdout.write(self.style.WARNING('No fighting-age birds available'))
            return 0

        fight_venues = [
            'Heritage Derby Arena',
            'Championship Coliseum',
            'Traditional Pit',
            'Valley Fighting Arena',
            'Elite Derby Center',
        ]

        opponent_names = [
            "Iron Mike's Warrior",
            'Valley Thunder',
            "Champion's Pride",
            'Lightning Strike',
            'Golden Blade',
            'Steel Storm',
            'Fire Dragon',
            'Thunder Beast',
            'Razor Edge',
            'Battle Hawk',
        ]

        fight_count = 0

        # Create historical completed fights
        completed_count = 8 if minimal else 20
        for i in range(min(completed_count, len(fighting_birds) * 3)):
            bird = random.choice(fighting_birds)

            # Historical date (last 18 months)
            days_ago = random.randint(30, 540)
            fight_date = timezone.now() - timedelta(days=days_ago)

            # Fight result (60% wins, 30% losses, 10% draws)
            result_roll = random.random()
            if result_roll < 0.6:
                result = 'win'
            elif result_roll < 0.9:
                result = 'loss'
            else:
                result = 'draw'

            fight = Fight.objects.create(
                fowl=bird,
                event_name=f'Heritage Derby {i+1}',
                arena_name=random.choice(fight_venues),
                arena_location=f'{random.choice(["Metro", "Valley", "Central"])} District',
                scheduled_datetime=fight_date,
                opponent_name=random.choice(opponent_names),
                opponent_breed=random.choice(['Hatch', 'Kelso', 'Sweater', 'Grey', 'Albany']),
                opponent_weight=Decimal(str(round(random.uniform(1.9, 2.4), 2))),
                status='completed',
                result=result,
                fight_duration_minutes=random.randint(5, 45),
                fowl_weight_at_fight=bird.weight,
                notes=f'Good fight, bird showed {"excellent" if result == "win" else "decent"} performance.',
            )
            fight_count += 1

        # Create scheduled upcoming fights
        upcoming_count = 3 if minimal else 8
        for i in range(min(upcoming_count, len(fighting_birds))):
            bird = fighting_birds[i]

            # Future date (next 3 months)
            days_ahead = random.randint(7, 90)
            fight_date = timezone.now() + timedelta(days=days_ahead)

            fight = Fight.objects.create(
                fowl=bird,
                event_name=f'Upcoming Derby {i+1}',
                arena_name=random.choice(fight_venues),
                arena_location=f'{random.choice(["Metro", "Valley", "Central"])} District',
                scheduled_datetime=fight_date,
                opponent_name=random.choice(opponent_names),
                opponent_breed=random.choice(['Hatch', 'Kelso', 'Sweater', 'Grey', 'Albany']),
                status='scheduled',
                fowl_weight_at_fight=bird.weight,
                notes='Scheduled match - preparations underway.',
            )
            fight_count += 1

        self.stdout.write(f'  Created: {fight_count} fight records')
        return fight_count

    def _validate_data_integrity(self):
        """Validate bloodline percentages and relationships."""
        self.stdout.write('Validating data integrity...')

        # Check bloodline percentages sum to 100%
        invalid_fowls = []
        for fowl in Gamefowl.objects.filter(owner__user__username='ms.hze'):
            total = fowl.bloodline_percentages.aggregate(
                total=models.Sum('percentage')
            )['total'] or Decimal('0')

            if abs(total - Decimal('100.00')) > Decimal('0.01'):
                invalid_fowls.append(f'{fowl.name} ({total}%)')

        if invalid_fowls:
            self.stdout.write(
                self.style.WARNING(
                    f'Warning: {len(invalid_fowls)} fowl with invalid bloodline percentages'
                )
            )
            for fowl_info in invalid_fowls[:3]:  # Show first 3
                self.stdout.write(f'  - {fowl_info}')
        else:
            self.stdout.write('  OK: All bloodline percentages valid')

        # Check sire/dam gender constraints
        invalid_lineages = []
        for fowl in Gamefowl.objects.filter(owner__user__username='ms.hze'):
            if fowl.sire and fowl.sire.gender != 'male':
                invalid_lineages.append(f'{fowl.name}: sire {fowl.sire.name} not male')
            if fowl.dam and fowl.dam.gender != 'female':
                invalid_lineages.append(f'{fowl.name}: dam {fowl.dam.name} not female')

        if invalid_lineages:
            self.stdout.write(
                self.style.ERROR(f'Error: {len(invalid_lineages)} invalid lineages found')
            )
        else:
            self.stdout.write('  OK: All lineage relationships valid')

    def _display_completion_message(self, user, profile, fowl_count, fight_count, bloodline_records):
        """Display the completion message with credentials."""
        self.stdout.write(
            self.style.SUCCESS('\n' + '=' * 48)
        )
        self.stdout.write(
            self.style.SUCCESS('SEED DATA CREATION COMPLETE!')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 48)
        )

        self.stdout.write(
            self.style.SUCCESS('\nAdmin User Created:')
        )
        self.stdout.write(f'   Username: {user.username}')
        self.stdout.write(f'   Password: HeritageFarm2024!')
        self.stdout.write(f'   Email: {user.email}')
        self.stdout.write(f'   Role: {profile.get_role_display()}')
        self.stdout.write(f'   Farm: {profile.farm_name}')

        if fowl_count > 0:
            self.stdout.write(
                self.style.SUCCESS('\nSample Data Created:')
            )
            self.stdout.write(f'   - {fowl_count} Gamefowl (Foundation + F1 + F2 generations)')
            self.stdout.write(f'   - {bloodline_records} Bloodline percentage records')
            self.stdout.write(f'   - {fight_count} Fight records (completed + scheduled)')
            self.stdout.write('   - Complete lineage relationships')

        self.stdout.write(
            self.style.SUCCESS('\nACCESS YOUR SYSTEM:')
        )
        self.stdout.write('   Main App: http://127.0.0.1:8000/')
        self.stdout.write('   Admin Panel: http://127.0.0.1:8000/admin/')

        self.stdout.write(
            self.style.SUCCESS('\nLOGIN INSTRUCTIONS:')
        )
        self.stdout.write('   1. Visit the admin panel or main app')
        self.stdout.write('   2. Login with: ms.hze / HeritageFarm2024!')
        self.stdout.write('   3. Explore the dashboard analytics')
        self.stdout.write('   4. View gamefowl lineage relationships')
        self.stdout.write('   5. Check fight records and statistics')

        self.stdout.write(
            self.style.SUCCESS('\n' + '=' * 48 + '\n')
        )