"""
Views for fights app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from apps.accounts.mixins import get_user_queryset
from apps.fowl.models import Gamefowl
from .models import Fight
from .forms import (
    FightScheduleForm, FightUpdateForm, FightResultForm, FightCancelForm
)


class FightListView(LoginRequiredMixin, ListView):
    """List all fights (filtered by user role)."""
    model = Fight
    template_name = 'fights/fight_list.html'
    context_object_name = 'fights'
    paginate_by = 15

    def get_queryset(self):
        # Get fights for user's fowl only (or all for admin)
        if self.request.user.profile.is_admin:
            queryset = Fight.objects.all()
        else:
            user_fowl = Gamefowl.objects.filter(owner=self.request.user.profile)
            queryset = Fight.objects.filter(fowl__in=user_fowl)

        queryset = queryset.select_related('fowl', 'fowl__owner')

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by result
        result = self.request.GET.get('result', '')
        if result:
            queryset = queryset.filter(result=result)

        # Filter by fowl
        fowl_id = self.request.GET.get('fowl', '')
        if fowl_id:
            queryset = queryset.filter(fowl_id=fowl_id)

        # Filter by date range
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(scheduled_datetime__date__gte=date_from)

        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(scheduled_datetime__date__lte=date_to)

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(fowl__name__icontains=search) |
                Q(arena_name__icontains=search) |
                Q(opponent_name__icontains=search) |
                Q(event_name__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's fowl for filter dropdown
        if self.request.user.profile.is_admin:
            context['fowl_choices'] = Gamefowl.objects.all()
        else:
            context['fowl_choices'] = Gamefowl.objects.filter(
                owner=self.request.user.profile
            )

        # Current filter values
        context['status_filter'] = self.request.GET.get('status', '')
        context['result_filter'] = self.request.GET.get('result', '')
        context['fowl_filter'] = self.request.GET.get('fowl', '')
        context['search'] = self.request.GET.get('search', '')

        context['status_choices'] = Fight.Status.choices
        context['result_choices'] = Fight.Result.choices

        # Quick stats
        base_qs = self.get_queryset()
        context['upcoming_count'] = base_qs.filter(
            status='scheduled',
            scheduled_datetime__gt=timezone.now()
        ).count()
        context['completed_count'] = base_qs.filter(status='completed').count()

        return context


class FightDetailView(LoginRequiredMixin, DetailView):
    """View fight details."""
    model = Fight
    template_name = 'fights/fight_detail.html'
    context_object_name = 'fight'

    def get_queryset(self):
        if self.request.user.profile.is_admin:
            return Fight.objects.all()
        user_fowl = Gamefowl.objects.filter(owner=self.request.user.profile)
        return Fight.objects.filter(fowl__in=user_fowl)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fight = self.object

        # Get other fights for this fowl
        context['fowl_other_fights'] = Fight.objects.filter(
            fowl=fight.fowl
        ).exclude(pk=fight.pk).order_by('-scheduled_datetime')[:5]

        return context


class FightCreateView(LoginRequiredMixin, CreateView):
    """Schedule a new fight."""
    model = Fight
    form_class = FightScheduleForm
    template_name = 'fights/fight_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user.profile
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select fowl if passed in URL
        fowl_id = self.request.GET.get('fowl')
        if fowl_id:
            initial['fowl'] = fowl_id
        return initial

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Fight scheduled for {form.instance.fowl.name}!'
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Schedule Fight'
        context['submit_text'] = 'Schedule Fight'
        return context


class FightUpdateView(LoginRequiredMixin, UpdateView):
    """Update fight details (before completion)."""
    model = Fight
    form_class = FightUpdateForm
    template_name = 'fights/fight_form.html'

    def get_queryset(self):
        if self.request.user.profile.is_admin:
            return Fight.objects.filter(status='scheduled')
        user_fowl = Gamefowl.objects.filter(owner=self.request.user.profile)
        return Fight.objects.filter(fowl__in=user_fowl, status='scheduled')

    def form_valid(self, form):
        messages.success(self.request, 'Fight details updated!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit Fight - {self.object.fowl.name}'
        context['submit_text'] = 'Save Changes'
        return context


class FightDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a scheduled fight."""
    model = Fight
    template_name = 'fights/fight_confirm_delete.html'
    success_url = reverse_lazy('fights:list')

    def get_queryset(self):
        if self.request.user.profile.is_admin:
            return Fight.objects.filter(status='scheduled')
        user_fowl = Gamefowl.objects.filter(owner=self.request.user.profile)
        return Fight.objects.filter(fowl__in=user_fowl, status='scheduled')

    def form_valid(self, form):
        messages.success(self.request, 'Scheduled fight deleted.')
        return super().form_valid(form)


@login_required
def fight_record_result(request, pk):
    """Record the result of a fight."""
    fight = get_object_or_404(Fight, pk=pk)

    # Check permission
    if (not request.user.profile.is_admin and
            fight.fowl.owner != request.user.profile):
        messages.error(request, "You don't have permission to update this fight.")
        return redirect('fights:list')

    # Check status
    if fight.status != Fight.Status.SCHEDULED:
        messages.error(request, "Can only record results for scheduled fights.")
        return redirect('fights:detail', pk=pk)

    if request.method == 'POST':
        form = FightResultForm(request.POST)
        if form.is_valid():
            fight.mark_completed(
                result=form.cleaned_data['result'],
                notes=form.cleaned_data.get('notes', ''),
                duration=form.cleaned_data.get('fight_duration_minutes'),
                fowl_weight=form.cleaned_data.get('fowl_weight_at_fight'),
            )
            messages.success(
                request,
                f'Result recorded: {fight.fowl.name} - {fight.get_result_display()}'
            )
            return redirect('fights:detail', pk=pk)
    else:
        form = FightResultForm(initial={
            'fowl_weight_at_fight': fight.fowl_weight_at_fight or fight.fowl.weight,
        })

    return render(request, 'fights/fight_result.html', {
        'fight': fight,
        'form': form,
    })


@login_required
def fight_cancel(request, pk):
    """Cancel a scheduled fight."""
    fight = get_object_or_404(Fight, pk=pk)

    # Check permission
    if (not request.user.profile.is_admin and
            fight.fowl.owner != request.user.profile):
        messages.error(request, "You don't have permission to cancel this fight.")
        return redirect('fights:list')

    # Check status
    if fight.status != Fight.Status.SCHEDULED:
        messages.error(request, "Can only cancel scheduled fights.")
        return redirect('fights:detail', pk=pk)

    if request.method == 'POST':
        form = FightCancelForm(request.POST)
        if form.is_valid():
            fight.mark_cancelled(reason=form.cleaned_data.get('reason', ''))
            messages.success(request, f'Fight for {fight.fowl.name} has been cancelled.')
            return redirect('fights:list')
    else:
        form = FightCancelForm()

    return render(request, 'fights/fight_cancel.html', {
        'fight': fight,
        'form': form,
    })


class UpcomingFightsView(LoginRequiredMixin, ListView):
    """List upcoming scheduled fights."""
    model = Fight
    template_name = 'fights/upcoming_fights.html'
    context_object_name = 'fights'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.profile.is_admin:
            queryset = Fight.objects.all()
        else:
            user_fowl = Gamefowl.objects.filter(owner=self.request.user.profile)
            queryset = Fight.objects.filter(fowl__in=user_fowl)

        return queryset.filter(
            status='scheduled',
            scheduled_datetime__gt=timezone.now()
        ).select_related('fowl').order_by('scheduled_datetime')
