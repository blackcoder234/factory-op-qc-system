"""
Context processor to make user roles and operational capabilities available in templates.
"""
from master_setup.rbac import (
    get_user_roles,
    has_any_role,
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
    ROLE_QA_INSPECTOR,
    ROLES_CAN_LOCK_WORKSTATIONS,
    ROLES_CAN_ACCEPT_BATCH,
    ROLES_CAN_APPROVE_INSPECTION,
    ROLES_CAN_APPROVE_DISPATCH,
)

def rbac_context(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'user_roles': set(),
            'primary_role': None,
            'can_lock_workstations': False,
            'can_accept_batch': False,
            'can_approve_inspection': False,
            'can_approve_dispatch': False,
        }
    
    roles = get_user_roles(user)
    primary_role = next(iter(roles), "Plant Supervisor" if user.is_staff else "Operator")

    return {
        'user_roles': roles,
        'primary_role': primary_role,
        'can_lock_workstations': user.is_superuser or has_any_role(user, *ROLES_CAN_LOCK_WORKSTATIONS),
        'can_accept_batch': user.is_superuser or has_any_role(user, *ROLES_CAN_ACCEPT_BATCH),
        'can_approve_inspection': user.is_superuser or has_any_role(user, *ROLES_CAN_APPROVE_INSPECTION),
        'can_approve_dispatch': user.is_superuser or has_any_role(user, *ROLES_CAN_APPROVE_DISPATCH),
    }
