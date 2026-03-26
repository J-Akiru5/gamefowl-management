"""
Admin configuration for fowl app.
"""
from django.contrib import admin
from .models import Bloodline, Gamefowl, FowlBloodline


class FowlBloodlineInline(admin.TabularInline):
    """Inline admin for fowl bloodline percentages."""
    model = FowlBloodline
    extra = 1
    autocomplete_fields = ['bloodline']


@admin.register(Bloodline)
class BloodlineAdmin(admin.ModelAdmin):
    """Admin for Bloodline model."""
    list_display = ('name', 'origin', 'is_predefined', 'created_by', 'created_at')
    list_filter = ('is_predefined', 'created_at')
    search_fields = ('name', 'origin', 'description')
    readonly_fields = ('created_at',)
    ordering = ('name',)


@admin.register(Gamefowl)
class GamefowlAdmin(admin.ModelAdmin):
    """Admin for Gamefowl model."""
    list_display = (
        'name', 'wing_band', 'gender', 'status', 'breed',
        'owner', 'sire', 'dam', 'created_at'
    )
    list_filter = ('gender', 'status', 'created_at')
    search_fields = ('name', 'wing_band', 'breed', 'owner__user__username')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['owner', 'sire', 'dam']
    inlines = [FowlBloodlineInline]
    ordering = ('-created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'wing_band', 'breed', 'gender', 'status', 'owner')
        }),
        ('Dates', {
            'fields': ('date_of_birth', 'date_of_death')
        }),
        ('Lineage', {
            'fields': ('sire', 'dam'),
            'description': 'Select the parents to enable automatic bloodline calculation.'
        }),
        ('Physical Attributes', {
            'fields': (
                'weight', 'height', 'leg_color', 'plumage_color',
                'plumage_pattern', 'eye_color', 'comb_type'
            ),
            'classes': ('collapse',)
        }),
        ('Image & Notes', {
            'fields': ('image', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'owner', 'owner__user', 'sire', 'dam'
        )


@admin.register(FowlBloodline)
class FowlBloodlineAdmin(admin.ModelAdmin):
    """Admin for FowlBloodline through model."""
    list_display = ('fowl', 'bloodline', 'percentage', 'is_manual_override')
    list_filter = ('is_manual_override', 'bloodline')
    search_fields = ('fowl__name', 'bloodline__name')
    autocomplete_fields = ['fowl', 'bloodline']
