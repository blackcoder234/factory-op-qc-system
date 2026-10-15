"""
FactoryOps QC — Role-Based Access Control (RBAC) Architecture
Enforces server-side permissions for the 5 standardized operational roles:
1. Plant / General Manager
2. Quality Engineer
3. Quality Manager
4. Shift Supervisor
5. QA Floor Inspector
"""

from functools import wraps
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

# Role Constants
ROLE_PLANT_MANAGER = "Plant / General Manager"
ROLE_QUALITY_ENGINEER = "Quality Engineer"
ROLE_QUALITY_MANAGER = "Quality Manager"
ROLE_SHIFT_SUPERVISOR = "Shift Supervisor"
ROLE_QA_INSPECTOR = "QA Floor Inspector"

ALL_ROLES = [
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
    ROLE_QA_INSPECTOR,
]

# Permission Mappings
ROLES_CAN_MANAGE_SETUP = [
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
]

ROLES_CAN_LOCK_WORKSTATIONS = [
    ROLE_PLANT_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_LOG_MAINTENANCE = [
    ROLE_SHIFT_SUPERVISOR,
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_RECEIVE_MATERIALS = [
    ROLE_QA_INSPECTOR,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
]

ROLES_CAN_VERIFY_MTC = [
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_ACCEPT_BATCH = [
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_QUARANTINE_BATCH = [
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_CREATE_CHECKLIST = [
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_START_INSPECTION = [
    ROLE_QA_INSPECTOR,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
]

ROLES_CAN_ENTER_READINGS = [
    ROLE_QA_INSPECTOR,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
]

ROLES_CAN_APPROVE_INSPECTION = [
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
]

ROLES_CAN_APPROVE_DISPATCH = [
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_MANAGER,
]


def get_user_roles(user):
    """Return a set of role names assigned to the given user."""
    if not user or not user.is_authenticated:
        return set()
    return set(user.groups.values_list('name', flat=True))


def has_any_role(user, *allowed_roles):
    """Check if the user has at least one of the specified roles or is a superuser."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    user_roles = get_user_roles(user)
    return any(role in user_roles for role in allowed_roles)


def role_required(*allowed_roles, redirect_url='master_setup:dashboard'):
    """
    View decorator that enforces authentication and role membership.
    Rejects unauthorized access with PermissionDenied (HTTP 403) or redirect with error.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.path}")
            
            if request.user.is_superuser or has_any_role(request.user, *allowed_roles):
                return view_func(request, *args, **kwargs)
            
            # Unauthorized access attempt
            messages.error(
                request,
                f"Access Denied: Your assigned role does not permit this operational action. Required: {', '.join(allowed_roles)}"
            )
            raise PermissionDenied(f"Access Denied. Required roles: {', '.join(allowed_roles)}")
        return _wrapped_view
    return decorator


def check_action_permission(user, *allowed_roles):
    """Helper to check permissions within a view for a specific action/POST branch."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return has_any_role(user, *allowed_roles)
