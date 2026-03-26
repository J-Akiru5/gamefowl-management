// Main JavaScript for Gamefowl Management System

// Mobile sidebar functionality is in base.html

// Generic utility functions
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('[data-auto-dismiss]');
    alerts.forEach(alert => {
        const delay = parseInt(alert.dataset.autoDismiss) || 5000;
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 300ms ease';
            setTimeout(() => alert.remove(), 300);
        }, delay);
    });

    // Form validation visual feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('invalid', function() {
                this.classList.add('border-red-500');
            });
            input.addEventListener('input', function() {
                if (this.validity.valid) {
                    this.classList.remove('border-red-500');
                }
            });
        });
    });
});

// Confirm delete actions
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}
