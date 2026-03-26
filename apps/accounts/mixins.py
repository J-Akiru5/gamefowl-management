"""
Mixins for role-based access control.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin that requires user to be an admin."""

    def test_func(self):
        return hasattr(self.request.user, 'profile') and self.request.user.profile.is_admin

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have permission to access this page.")
        return super().handle_no_permission()


class OwnerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that allows access to admins or the owner of the object.
    Requires the view to have a get_object() method.
    """
    owner_field = 'owner'  # Default field name for owner FK

    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False

        # Admins can access anything
        if self.request.user.profile.is_admin:
            return True

        # Check if user is the owner
        obj = self.get_object()
        owner = getattr(obj, self.owner_field, None)

        if owner is None:
            return False

        # owner could be a User or UserProfile
        if hasattr(owner, 'user'):
            return owner.user == self.request.user
        return owner == self.request.user.profile

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("You don't have permission to access this resource.")
        return super().handle_no_permission()


def get_user_queryset(user, model, owner_field='owner'):
    """
    Helper function to filter queryset based on user role.
    Admins see all, breeders see only their own.
    """
    if not hasattr(user, 'profile'):
        return model.objects.none()

    if user.profile.is_admin:
        return model.objects.all()

    # Filter by owner
    filter_kwargs = {owner_field: user.profile}
    return model.objects.filter(**filter_kwargs)
