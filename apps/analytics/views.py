"""
Views for analytics dashboard.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.fowl.models import Gamefowl
from apps.fights.models import Fight
from .services import (
    generate_win_loss_chart,
    generate_fights_per_month_chart,
    generate_breed_distribution_chart,
    generate_bloodline_distribution_chart,
    generate_fowl_status_chart,
    generate_performance_trend_chart,
    get_dashboard_stats,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main analytics dashboard - landing page."""
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile
        is_admin = user_profile.is_admin

        # Get querysets based on role
        if is_admin:
            fowl_qs = Gamefowl.objects.all()
            fights_qs = Fight.objects.all()
        else:
            fowl_qs = Gamefowl.objects.filter(owner=user_profile)
            fowl_ids = fowl_qs.values_list('id', flat=True)
            fights_qs = Fight.objects.filter(fowl_id__in=fowl_ids)

        # Summary statistics
        context['stats'] = get_dashboard_stats(user_profile)

        # Generate charts
        context['win_loss_chart'] = generate_win_loss_chart(fights_qs)
        context['fights_per_month_chart'] = generate_fights_per_month_chart(fights_qs)
        context['breed_distribution_chart'] = generate_breed_distribution_chart(fowl_qs)
        context['fowl_status_chart'] = generate_fowl_status_chart(fowl_qs)
        context['performance_trend_chart'] = generate_performance_trend_chart(fights_qs)
        context['bloodline_chart'] = generate_bloodline_distribution_chart(fowl_qs)

        # Recent activity
        context['recent_fights'] = fights_qs.filter(
            status='completed'
        ).select_related('fowl').order_by('-completed_at', '-updated_at')[:5]

        context['upcoming_fights'] = fights_qs.filter(
            status='scheduled'
        ).select_related('fowl').order_by('scheduled_datetime')[:5]

        context['recent_fowl'] = fowl_qs.select_related('owner').order_by('-created_at')[:5]

        # Role indicator
        context['is_admin'] = is_admin

        return context


class PerformanceReportView(LoginRequiredMixin, TemplateView):
    """Detailed performance report page."""
    template_name = 'analytics/performance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile
        is_admin = user_profile.is_admin

        # Get querysets based on role
        if is_admin:
            fowl_qs = Gamefowl.objects.all()
            fights_qs = Fight.objects.all()
        else:
            fowl_qs = Gamefowl.objects.filter(owner=user_profile)
            fowl_ids = fowl_qs.values_list('id', flat=True)
            fights_qs = Fight.objects.filter(fowl_id__in=fowl_ids)

        # Top performers (by win rate, min 3 fights)
        from django.db.models import Count, Q, F

        fowl_with_stats = fowl_qs.annotate(
            total_fights=Count('fights', filter=Q(fights__status='completed')),
            wins=Count('fights', filter=Q(fights__result='win')),
        ).filter(total_fights__gte=3).order_by('-wins')[:10]

        context['top_performers'] = fowl_with_stats

        # Charts
        context['win_loss_chart'] = generate_win_loss_chart(fights_qs)
        context['performance_trend_chart'] = generate_performance_trend_chart(fights_qs, months=12)
        context['bloodline_chart'] = generate_bloodline_distribution_chart(fowl_qs)

        # Stats
        context['stats'] = get_dashboard_stats(user_profile)

        return context
