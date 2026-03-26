"""
Gamefowl models with lineage and bloodline tracking.
This is the core of the application.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from apps.accounts.models import UserProfile


class Bloodline(models.Model):
    """
    Named bloodline strains (Hatch, Kelso, Sweater, etc.)
    Can be predefined (seeded) or user-created.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    origin = models.CharField(
        max_length=100,
        blank=True,
        help_text="Origin breeder or country of this bloodline"
    )
    is_predefined = models.BooleanField(
        default=False,
        help_text="System-seeded bloodline (cannot be deleted)"
    )
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_bloodlines'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Bloodline'
        verbose_name_plural = 'Bloodlines'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('fowl:bloodline_detail', kwargs={'pk': self.pk})


class Gamefowl(models.Model):
    """
    Core gamefowl model with self-referential lineage tracking.
    Supports tracking ancestry through sire (father) and dam (mother) relationships.
    """

    class Gender(models.TextChoices):
        MALE = 'male', 'Stag/Cock'
        FEMALE = 'female', 'Pullet/Hen'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        BREEDING = 'breeding', 'Breeding'
        RETIRED = 'retired', 'Retired'
        DECEASED = 'deceased', 'Deceased'
        SOLD = 'sold', 'Sold'

    # ============ BASIC INFO ============
    name = models.CharField(max_length=100)
    wing_band = models.CharField(
        max_length=50,
        blank=True,
        help_text="Unique wing band ID for identification"
    )
    breed = models.CharField(
        max_length=100,
        blank=True,
        help_text="General breed classification"
    )
    gender = models.CharField(max_length=10, choices=Gender.choices)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # ============ OWNERSHIP ============
    owner = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='fowls'
    )

    # ============ LINEAGE (Self-referential FKs) ============
    sire = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sire_offspring',
        limit_choices_to={'gender': 'male'},
        help_text="Father (must be male)"
    )
    dam = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dam_offspring',
        limit_choices_to={'gender': 'female'},
        help_text="Mother (must be female)"
    )

    # ============ PHYSICAL ATTRIBUTES ============
    weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Weight in kilograms"
    )
    height = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Height in centimeters"
    )
    leg_color = models.CharField(max_length=50, blank=True)
    plumage_color = models.CharField(max_length=100, blank=True)
    plumage_pattern = models.CharField(max_length=100, blank=True)
    eye_color = models.CharField(max_length=50, blank=True)
    comb_type = models.CharField(max_length=50, blank=True)

    # ============ IMAGE ============
    image = models.ImageField(
        upload_to='fowl/%Y/%m/',
        blank=True,
        null=True
    )

    # ============ NOTES ============
    notes = models.TextField(blank=True)

    # ============ TIMESTAMPS ============
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gamefowl'
        verbose_name_plural = 'Gamefowl'

    def __str__(self):
        if self.wing_band:
            return f"{self.name} ({self.wing_band})"
        return self.name

    def get_absolute_url(self):
        return reverse('fowl:detail', kwargs={'pk': self.pk})

    # ============ LINEAGE HELPER PROPERTIES ============

    @property
    def full_siblings(self):
        """
        Get fowl sharing BOTH sire and dam.
        Returns QuerySet, empty if either parent is missing.
        """
        if not self.sire or not self.dam:
            return Gamefowl.objects.none()
        return Gamefowl.objects.filter(
            sire=self.sire,
            dam=self.dam
        ).exclude(pk=self.pk)

    @property
    def half_siblings_sire(self):
        """
        Get fowl sharing only the sire (different dam).
        Returns QuerySet, empty if sire is missing.
        """
        if not self.sire:
            return Gamefowl.objects.none()
        qs = Gamefowl.objects.filter(sire=self.sire).exclude(pk=self.pk)
        if self.dam:
            qs = qs.exclude(dam=self.dam)
        return qs

    @property
    def half_siblings_dam(self):
        """
        Get fowl sharing only the dam (different sire).
        Returns QuerySet, empty if dam is missing.
        """
        if not self.dam:
            return Gamefowl.objects.none()
        qs = Gamefowl.objects.filter(dam=self.dam).exclude(pk=self.pk)
        if self.sire:
            qs = qs.exclude(sire=self.sire)
        return qs

    @property
    def all_siblings(self):
        """Get all siblings (full + half from both parents)."""
        from django.db.models import Q

        if not self.sire and not self.dam:
            return Gamefowl.objects.none()

        q = Q()
        if self.sire:
            q |= Q(sire=self.sire)
        if self.dam:
            q |= Q(dam=self.dam)

        return Gamefowl.objects.filter(q).exclude(pk=self.pk).distinct()

    @property
    def offspring(self):
        """Get all direct children of this fowl."""
        if self.gender == self.Gender.MALE:
            return self.sire_offspring.all()
        return self.dam_offspring.all()

    @property
    def offspring_count(self):
        """Get count of direct children."""
        return self.offspring.count()

    def get_ancestors(self, generations=3):
        """
        Get ancestors up to N generations.
        Returns dict with structure:
        {
            'sire': {...},
            'dam': {...},
        }
        """
        if generations <= 0:
            return None

        ancestors = {}
        if self.sire:
            ancestors['sire'] = {
                'fowl': self.sire,
                'parents': self.sire.get_ancestors(generations - 1)
            }
        if self.dam:
            ancestors['dam'] = {
                'fowl': self.dam,
                'parents': self.dam.get_ancestors(generations - 1)
            }

        return ancestors if ancestors else None

    def get_descendants(self, generations=3):
        """
        Get descendants up to N generations.
        Returns list of fowl with generation level.
        """
        descendants = []

        def collect_descendants(fowl, gen_level):
            if gen_level > generations:
                return
            for child in fowl.offspring:
                descendants.append({
                    'fowl': child,
                    'generation': gen_level
                })
                collect_descendants(child, gen_level + 1)

        collect_descendants(self, 1)
        return descendants

    @property
    def age_display(self):
        """Get age as human-readable string."""
        from datetime import date

        if not self.date_of_birth:
            return "Unknown"

        end_date = self.date_of_death if self.date_of_death else date.today()
        delta = end_date - self.date_of_birth

        years = delta.days // 365
        months = (delta.days % 365) // 30

        if years > 0:
            if months > 0:
                return f"{years}y {months}m"
            return f"{years}y"
        elif months > 0:
            return f"{months}m"
        else:
            return f"{delta.days}d"

    @property
    def bloodline_summary(self):
        """Get formatted bloodline percentage summary."""
        bloodlines = self.bloodline_percentages.all()
        if not bloodlines:
            return "No bloodline data"

        parts = [f"{bl.percentage:.1f}% {bl.bloodline.name}" for bl in bloodlines]
        return ", ".join(parts)


class FowlBloodline(models.Model):
    """
    Through model for Gamefowl <-> Bloodline M2M relationship.
    Stores the percentage of each bloodline strain in a fowl.

    Example: A fowl might be 50% Hatch, 25% Kelso, 25% Sweater
    Total percentages should sum to 100 (enforced at form level).
    """
    fowl = models.ForeignKey(
        Gamefowl,
        on_delete=models.CASCADE,
        related_name='bloodline_percentages'
    )
    bloodline = models.ForeignKey(
        Bloodline,
        on_delete=models.CASCADE,
        related_name='fowl_percentages'
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of this bloodline (0-100)"
    )
    is_manual_override = models.BooleanField(
        default=False,
        help_text="True if user manually set this, bypassing auto-calculation"
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['fowl', 'bloodline']
        ordering = ['-percentage']
        verbose_name = 'Fowl Bloodline'
        verbose_name_plural = 'Fowl Bloodlines'

    def __str__(self):
        return f"{self.fowl.name}: {self.percentage}% {self.bloodline.name}"
