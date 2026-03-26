"""
Views for fowl app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count

from apps.accounts.mixins import OwnerOrAdminMixin, get_user_queryset
from .models import Gamefowl, Bloodline, FowlBloodline
from .forms import GamefowlForm, BloodlineForm, FowlBloodlineFormSet
from .services import get_bloodline_breakdown, save_calculated_bloodlines


# ============ GAMEFOWL VIEWS ============

class FowlListView(LoginRequiredMixin, ListView):
    """List all gamefowl (filtered by user role)."""
    model = Gamefowl
    template_name = 'fowl/fowl_list.html'
    context_object_name = 'fowls'
    paginate_by = 12

    def get_queryset(self):
        queryset = get_user_queryset(self.request.user, Gamefowl, 'owner')
        queryset = queryset.select_related('owner', 'sire', 'dam')

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(wing_band__icontains=search) |
                Q(breed__icontains=search)
            )

        # Filter by gender
        gender = self.request.GET.get('gender', '')
        if gender:
            queryset = queryset.filter(gender=gender)

        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['gender_filter'] = self.request.GET.get('gender', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['gender_choices'] = Gamefowl.Gender.choices
        context['status_choices'] = Gamefowl.Status.choices
        return context


class FowlDetailView(OwnerOrAdminMixin, DetailView):
    """View fowl details including lineage and bloodlines."""
    model = Gamefowl
    template_name = 'fowl/fowl_detail.html'
    context_object_name = 'fowl'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fowl = self.object

        # Lineage data
        context['ancestors'] = fowl.get_ancestors(generations=3)
        context['full_siblings'] = fowl.full_siblings[:6]
        context['half_siblings_sire'] = fowl.half_siblings_sire[:6]
        context['half_siblings_dam'] = fowl.half_siblings_dam[:6]
        context['offspring'] = fowl.offspring[:6]

        # Bloodline data
        context['bloodline_data'] = get_bloodline_breakdown(fowl)

        # Fight history
        context['recent_fights'] = fowl.fights.all()[:5]
        context['fight_stats'] = {
            'total': fowl.fights.count(),
            'wins': fowl.fights.filter(result='win').count(),
            'losses': fowl.fights.filter(result='loss').count(),
        }

        return context


class FowlCreateView(LoginRequiredMixin, CreateView):
    """Create a new gamefowl."""
    model = Gamefowl
    form_class = GamefowlForm
    template_name = 'fowl/fowl_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user.profile
        messages.success(self.request, f'"{form.instance.name}" has been added!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Fowl'
        context['submit_text'] = 'Add Fowl'
        return context


class FowlUpdateView(OwnerOrAdminMixin, UpdateView):
    """Update an existing gamefowl."""
    model = Gamefowl
    form_class = GamefowlForm
    template_name = 'fowl/fowl_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.object.owner
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'"{form.instance.name}" has been updated!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        context['submit_text'] = 'Save Changes'
        return context


class FowlDeleteView(OwnerOrAdminMixin, DeleteView):
    """Delete a gamefowl."""
    model = Gamefowl
    template_name = 'fowl/fowl_confirm_delete.html'
    success_url = reverse_lazy('fowl:list')

    def form_valid(self, form):
        messages.success(self.request, f'"{self.object.name}" has been deleted.')
        return super().form_valid(form)


@login_required
def fowl_bloodlines_edit(request, pk):
    """Edit bloodline percentages for a fowl."""
    fowl = get_object_or_404(Gamefowl, pk=pk)

    # Check permission
    if not request.user.profile.is_admin and fowl.owner != request.user.profile:
        messages.error(request, "You don't have permission to edit this fowl.")
        return redirect('fowl:detail', pk=pk)

    if request.method == 'POST':
        formset = FowlBloodlineFormSet(request.POST, instance=fowl)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Bloodline percentages updated!')
            return redirect('fowl:detail', pk=pk)
    else:
        formset = FowlBloodlineFormSet(instance=fowl)

    return render(request, 'fowl/fowl_bloodlines_edit.html', {
        'fowl': fowl,
        'formset': formset,
        'bloodline_data': get_bloodline_breakdown(fowl),
    })


@login_required
def fowl_recalculate_bloodlines(request, pk):
    """Force recalculate bloodlines from parents."""
    fowl = get_object_or_404(Gamefowl, pk=pk)

    # Check permission
    if not request.user.profile.is_admin and fowl.owner != request.user.profile:
        messages.error(request, "You don't have permission to modify this fowl.")
        return redirect('fowl:detail', pk=pk)

    save_calculated_bloodlines(fowl, force_recalculate=True)
    messages.success(request, 'Bloodlines recalculated from parents!')
    return redirect('fowl:detail', pk=pk)


# ============ BLOODLINE VIEWS ============

class BloodlineListView(LoginRequiredMixin, ListView):
    """List all bloodlines."""
    model = Bloodline
    template_name = 'fowl/bloodline_list.html'
    context_object_name = 'bloodlines'
    paginate_by = 20

    def get_queryset(self):
        queryset = Bloodline.objects.annotate(
            fowl_count=Count('fowl_percentages')
        )

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(origin__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class BloodlineDetailView(LoginRequiredMixin, DetailView):
    """View bloodline details and fowl with this bloodline."""
    model = Bloodline
    template_name = 'fowl/bloodline_detail.html'
    context_object_name = 'bloodline'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get fowl with this bloodline (filtered by user)
        fowl_bloodlines = self.object.fowl_percentages.select_related(
            'fowl', 'fowl__owner'
        ).order_by('-percentage')

        if not self.request.user.profile.is_admin:
            fowl_bloodlines = fowl_bloodlines.filter(
                fowl__owner=self.request.user.profile
            )

        context['fowl_bloodlines'] = fowl_bloodlines[:20]
        return context


class BloodlineCreateView(LoginRequiredMixin, CreateView):
    """Create a new bloodline."""
    model = Bloodline
    form_class = BloodlineForm
    template_name = 'fowl/bloodline_form.html'
    success_url = reverse_lazy('fowl:bloodline_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user.profile
        messages.success(self.request, f'Bloodline "{form.instance.name}" created!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Bloodline'
        context['submit_text'] = 'Create Bloodline'
        return context


class BloodlineUpdateView(LoginRequiredMixin, UpdateView):
    """Update a bloodline."""
    model = Bloodline
    form_class = BloodlineForm
    template_name = 'fowl/bloodline_form.html'
    success_url = reverse_lazy('fowl:bloodline_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Only admins can edit predefined bloodlines
        if obj.is_predefined and not request.user.profile.is_admin:
            messages.error(request, "Cannot edit predefined bloodlines.")
            return redirect('fowl:bloodline_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Bloodline "{form.instance.name}" updated!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit {self.object.name}'
        context['submit_text'] = 'Save Changes'
        return context


class BloodlineDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a bloodline."""
    model = Bloodline
    template_name = 'fowl/bloodline_confirm_delete.html'
    success_url = reverse_lazy('fowl:bloodline_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_predefined:
            messages.error(request, "Cannot delete predefined bloodlines.")
            return redirect('fowl:bloodline_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Bloodline "{self.object.name}" deleted.')
        return super().form_valid(form)
