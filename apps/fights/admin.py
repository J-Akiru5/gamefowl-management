"""
Admin configuration for fights app.
"""
from django.contrib import admin
from .models import Fight


@admin.register(Fight)
class FightAdmin(admin.ModelAdmin):
    """Admin for Fight model."""
    list_display = (
        'fowl', 'arena_name', 'scheduled_datetime', 'status',
        'result', 'opponent_name', 'created_at'
    )
    list_filter = ('status', 'result', 'scheduled_datetime', 'arena_name')
    search_fields = (
        'fowl__name', 'fowl__wing_band', 'arena_name',
        'opponent_name', 'event_name'
    )
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    autocomplete_fields = ['fowl']
    ordering = ('-scheduled_datetime',)
    date_hierarchy = 'scheduled_datetime'

    fieldsets = (
        ('Fight Information', {
            'fields': ('fowl', 'event_name', 'arena_name', 'arena_location', 'scheduled_datetime')
        }),
        ('Opponent', {
            'fields': ('opponent_name', 'opponent_breed', 'opponent_weight')
        }),
        ('Status & Result', {
            'fields': ('status', 'result', 'completed_at')
        }),
        ('Details', {
            'fields': ('fowl_weight_at_fight', 'fight_duration_minutes', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('fowl', 'fowl__owner')

    actions = ['mark_as_completed', 'mark_as_cancelled']

    @admin.action(description='Mark selected fights as completed')
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='scheduled').update(status='completed')
        self.message_user(request, f'{updated} fight(s) marked as completed.')

    @admin.action(description='Mark selected fights as cancelled')
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status='scheduled').update(status='cancelled')
        self.message_user(request, f'{updated} fight(s) marked as cancelled.')
