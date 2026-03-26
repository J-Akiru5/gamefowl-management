"""
Fight scheduling and records models.
Single model with status transitions: SCHEDULED -> COMPLETED or CANCELLED
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.fowl.models import Gamefowl


class Fight(models.Model):
    """
    Single model for both scheduling and recording fights.
    Status transitions: SCHEDULED -> COMPLETED or CANCELLED
    """

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class Result(models.TextChoices):
        WIN = 'win', 'Win'
        LOSS = 'loss', 'Loss'
        DRAW = 'draw', 'Draw'
        NO_CONTEST = 'no_contest', 'No Contest'

    # ============ CORE FIELDS ============
    fowl = models.ForeignKey(
        Gamefowl,
        on_delete=models.CASCADE,
        related_name='fights'
    )

    # ============ SCHEDULING INFO ============
    event_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the derby or event"
    )
    arena_name = models.CharField(max_length=200)
    arena_location = models.CharField(max_length=300, blank=True)
    scheduled_datetime = models.DateTimeField()

    # ============ OPPONENT INFO ============
    opponent_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Opponent fowl name or owner"
    )
    opponent_breed = models.CharField(max_length=100, blank=True)
    opponent_weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Opponent weight in kg"
    )

    # ============ STATUS AND RESULT ============
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        blank=True
    )

    # ============ FIGHT DETAILS (filled after completion) ============
    fight_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration of fight in minutes"
    )
    notes = models.TextField(
        blank=True,
        help_text="Fight notes, observations, performance details"
    )

    # Weight at time of fight (may differ from current weight)
    fowl_weight_at_fight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Fowl's weight at time of fight in kg"
    )

    # ============ TIMESTAMPS ============
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the fight result was recorded"
    )

    class Meta:
        ordering = ['-scheduled_datetime']
        verbose_name = 'Fight'
        verbose_name_plural = 'Fights'

    def __str__(self):
        date_str = self.scheduled_datetime.strftime('%Y-%m-%d')
        return f"{self.fowl.name} @ {self.arena_name} ({date_str})"

    def get_absolute_url(self):
        return reverse('fights:detail', kwargs={'pk': self.pk})

    # ============ STATUS HELPERS ============

    @property
    def is_upcoming(self):
        """Check if this is a future scheduled fight."""
        return (
            self.status == self.Status.SCHEDULED and
            self.scheduled_datetime > timezone.now()
        )

    @property
    def is_past_due(self):
        """Check if scheduled fight is past its date but not completed."""
        return (
            self.status == self.Status.SCHEDULED and
            self.scheduled_datetime <= timezone.now()
        )

    @property
    def is_completed(self):
        """Check if fight is completed."""
        return self.status == self.Status.COMPLETED

    @property
    def is_win(self):
        """Check if result was a win."""
        return self.result == self.Result.WIN

    @property
    def is_loss(self):
        """Check if result was a loss."""
        return self.result == self.Result.LOSS

    # ============ DISPLAY HELPERS ============

    @property
    def result_display(self):
        """Get result with appropriate styling class."""
        if not self.result:
            return {'text': '-', 'class': 'text-gray-500'}

        classes = {
            'win': 'text-green-600 font-bold',
            'loss': 'text-red-600 font-bold',
            'draw': 'text-yellow-600',
            'no_contest': 'text-gray-600',
        }
        return {
            'text': self.get_result_display(),
            'class': classes.get(self.result, 'text-gray-500')
        }

    @property
    def status_badge_class(self):
        """Get CSS class for status badge."""
        classes = {
            'scheduled': 'bg-blue-100 text-blue-800',
            'completed': 'bg-green-100 text-green-800',
            'cancelled': 'bg-gray-100 text-gray-800',
        }
        return classes.get(self.status, 'bg-gray-100 text-gray-800')

    @property
    def days_until(self):
        """Get days until scheduled fight (negative if past)."""
        if self.status != self.Status.SCHEDULED:
            return None
        delta = self.scheduled_datetime.date() - timezone.now().date()
        return delta.days

    # ============ ACTIONS ============

    def mark_completed(self, result, notes='', duration=None, fowl_weight=None):
        """
        Mark fight as completed with result.
        """
        self.status = self.Status.COMPLETED
        self.result = result
        self.completed_at = timezone.now()

        if notes:
            self.notes = notes
        if duration is not None:
            self.fight_duration_minutes = duration
        if fowl_weight is not None:
            self.fowl_weight_at_fight = fowl_weight

        self.save()

    def mark_cancelled(self, reason=''):
        """Mark fight as cancelled."""
        self.status = self.Status.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}"
        self.save()
