"""
Management command to seed predefined bloodlines.
Run with: python manage.py seed_bloodlines
"""
from django.core.management.base import BaseCommand
from apps.fowl.models import Bloodline


PREDEFINED_BLOODLINES = [
    {
        "name": "Hatch",
        "origin": "Sanford Hatch, USA",
        "description": "Known for power, cutting ability, and gameness. One of the most popular fighting lines worldwide."
    },
    {
        "name": "Kelso",
        "origin": "Walter Kelso, USA",
        "description": "Smart, ring-wise fighters known for their intelligence and side-stepping ability."
    },
    {
        "name": "Sweater",
        "origin": "Carol Nesmith, USA",
        "description": "Known for speed, agility, and high-flying attacks. Excellent cutting ability."
    },
    {
        "name": "Roundhead",
        "origin": "John Garner / Lacy, USA",
        "description": "Aggressive and powerful fighters. Known for their gameness and deadly cutting."
    },
    {
        "name": "Albany",
        "origin": "Murphy's Bloodline, USA",
        "description": "Well-balanced fighters combining power, speed, and intelligence."
    },
    {
        "name": "Grey",
        "origin": "Various breeders",
        "description": "Known for intelligence, cutting ability, and ability to finish fights quickly."
    },
    {
        "name": "Claret",
        "origin": "Various breeders",
        "description": "Known for deep gameness, endurance, and never-give-up attitude."
    },
    {
        "name": "Butcher",
        "origin": "USA",
        "description": "Known for power, stamina, and ability to fight at long range."
    },
    {
        "name": "Radio",
        "origin": "USA",
        "description": "Fast starters and early finishers. Known for quick, aggressive attacks."
    },
    {
        "name": "Asil",
        "origin": "India / Middle East",
        "description": "One of the oldest fighting breeds. Known for power, courage, and endurance."
    },
    {
        "name": "Lemon",
        "origin": "USA",
        "description": "Distinguished by their lemon hackle coloring. Known for speed and cutting."
    },
    {
        "name": "Whitehackle",
        "origin": "USA",
        "description": "Known for gameness, power, and beautiful white hackle feathers."
    },
    {
        "name": "Brown Red",
        "origin": "USA",
        "description": "Aggressive fighters with excellent cutting ability and gameness."
    },
    {
        "name": "Mug",
        "origin": "USA",
        "description": "Known for their durability and ability to absorb punishment while fighting."
    },
    {
        "name": "Blueface",
        "origin": "USA",
        "description": "Named for their blue-tinted faces. Smart and accurate fighters."
    },
]


class Command(BaseCommand):
    help = 'Seed the database with predefined bloodlines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing predefined bloodlines before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            deleted_count, _ = Bloodline.objects.filter(is_predefined=True).delete()
            self.stdout.write(
                self.style.WARNING(f'Cleared {deleted_count} existing predefined bloodlines')
            )

        created_count = 0
        updated_count = 0

        for bl_data in PREDEFINED_BLOODLINES:
            bloodline, created = Bloodline.objects.update_or_create(
                name=bl_data['name'],
                defaults={
                    'origin': bl_data['origin'],
                    'description': bl_data['description'],
                    'is_predefined': True,
                    'created_by': None,  # System-created
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'  Created: {bloodline.name}')
            else:
                updated_count += 1
                self.stdout.write(f'  Updated: {bloodline.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Total predefined bloodlines: {Bloodline.objects.filter(is_predefined=True).count()}'
            )
        )
