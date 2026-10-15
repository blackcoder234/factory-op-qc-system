from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import MaterialBatch, ChemicalComposition, MechanicalProperties, SupplierNonConformance
from .forms import (
    MaterialBatchForm,
    ChemicalCompositionForm,
    MechanicalPropertiesForm,
    SupplierNonConformanceForm,
    MtcDocumentUploadForm,
)

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from master_setup.rbac import (
    check_action_permission,
    ROLES_CAN_RECEIVE_MATERIALS,
    ROLES_CAN_VERIFY_MTC,
    ROLES_CAN_ACCEPT_BATCH,
    ROLES_CAN_QUARANTINE_BATCH,
)


@login_required(login_url='master_setup:login')
def batch_list(request):
    """Module 3: Raw Material Intake Dock Receiving List & Quick Logging."""
    batches = MaterialBatch.objects.select_related('part').all()

    if request.method == 'POST':
        if not check_action_permission(request.user, *ROLES_CAN_RECEIVE_MATERIALS):
            raise PermissionDenied("Access Denied: Your assigned role does not permit logging inward raw material batches.")
        
        form = MaterialBatchForm(request.POST, request.FILES)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f'Material Batch "{batch.heat_number}" received and logged at dock!')
            return redirect('material_intake:batch_detail', batch_id=batch.id)
    else:
        form = MaterialBatchForm()

    pending_count = batches.filter(status='PENDING').count()
    accepted_count = batches.filter(status='ACCEPTED').count()
    rejected_count = batches.filter(status__in=['REJECTED', 'QUARANTINED']).count()

    return render(request, 'material_intake/batch_list.html', {
        'batches': batches,
        'form': form,
        'pending_count': pending_count,
        'accepted_count': accepted_count,
        'rejected_count': rejected_count,
    })


@login_required(login_url='master_setup:login')
def batch_detail(request, batch_id):
    """MTC Verification Workspace: Chemical & Mechanical property testing and Acceptance Gating."""
    batch = get_object_or_404(MaterialBatch, pk=batch_id)

    # Get or create related chemistry and mechanics
    chemistry, _ = ChemicalComposition.objects.get_or_create(
        batch=batch,
        defaults={'carbon': 0.0, 'manganese': 0.0, 'silicon': 0.0}
    )
    mechanics, _ = MechanicalProperties.objects.get_or_create(
        batch=batch,
        defaults={'tensile_strength': 0.0, 'yield_strength': 0.0, 'elongation': 0.0, 'hardness': 0.0}
    )

    chem_form = ChemicalCompositionForm(instance=chemistry)
    mech_form = MechanicalPropertiesForm(instance=mechanics)
    mtc_form = MtcDocumentUploadForm(instance=batch)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload_mtc':
            if not check_action_permission(request.user, *ROLES_CAN_VERIFY_MTC, *ROLES_CAN_RECEIVE_MATERIALS):
                raise PermissionDenied("Access Denied: Your assigned role does not permit uploading MTC certificates.")
            
            mtc_form = MtcDocumentUploadForm(request.POST, request.FILES, instance=batch)
            if mtc_form.is_valid():
                mtc_form.save()
                messages.success(request, f'Mill Test Certificate (MTC) successfully attached to Heat# {batch.heat_number}.')
                return redirect('material_intake:batch_detail', batch_id=batch.id)
            else:
                for field, errs in mtc_form.errors.items():
                    for err in errs:
                        messages.error(request, f"MTC Upload Error: {err}")

        elif action == 'save_chemistry':
            if not check_action_permission(request.user, *ROLES_CAN_VERIFY_MTC):
                raise PermissionDenied("Access Denied: Only Quality Engineers or Quality Managers can record MTC chemistry analysis.")
            
            chem_form = ChemicalCompositionForm(request.POST, instance=chemistry)
            if chem_form.is_valid():
                c = chem_form.save(commit=False)
                if c.is_composition_ok:
                    c.verified_at = timezone.now()
                c.save()
                messages.success(request, 'Chemical composition verified and updated!')
                return redirect('material_intake:batch_detail', batch_id=batch.id)
            else:
                for field, errs in chem_form.errors.items():
                    for err in errs:
                        messages.error(request, f"Chemistry Form Error ({field}): {err}")

        elif action == 'save_mechanics':
            if not check_action_permission(request.user, *ROLES_CAN_VERIFY_MTC):
                raise PermissionDenied("Access Denied: Only Quality Engineers or Quality Managers can record mechanical verification.")

            mech_form = MechanicalPropertiesForm(request.POST, instance=mechanics)
            if mech_form.is_valid():
                m = mech_form.save(commit=False)
                if m.is_properties_ok:
                    m.verified_at = timezone.now()
                m.save()
                messages.success(request, 'Mechanical properties verified and updated!')
                return redirect('material_intake:batch_detail', batch_id=batch.id)
            else:
                for field, errs in mech_form.errors.items():
                    for err in errs:
                        messages.error(request, f"Mechanical Form Error ({field}): {err}")

        elif action == 'accept_batch':
            if not check_action_permission(request.user, *ROLES_CAN_ACCEPT_BATCH):
                raise PermissionDenied("Access Denied: Only Quality Managers can authorize material release and batch acceptance.")
            
            # Strict Server-Side Acceptance Gate
            blockers = batch.get_acceptance_blockers()
            if blockers:
                for blocker in blockers:
                    messages.error(request, f"Acceptance Blocked: {blocker}")
                return redirect('material_intake:batch_detail', batch_id=batch.id)

            batch.status = 'ACCEPTED'
            batch.save()
            messages.success(request, f'Batch {batch.heat_number} successfully ACCEPTED and released to production!')
            return redirect('material_intake:batch_detail', batch_id=batch.id)

        elif action == 'quarantine_batch':
            if not check_action_permission(request.user, *ROLES_CAN_QUARANTINE_BATCH):
                raise PermissionDenied("Access Denied: Only Quality Engineers or Quality Managers can quarantine material.")

            batch.status = 'QUARANTINED'
            batch.save()
            messages.warning(request, f'Batch {batch.heat_number} marked as QUARANTINED in quality hold!')
            return redirect('material_intake:raise_sncr', batch_id=batch.id)

    sncrs = batch.non_conformances.all()
    blockers = batch.get_acceptance_blockers()

    return render(request, 'material_intake/batch_detail.html', {
        'batch': batch,
        'chemistry': chemistry,
        'mechanics': mechanics,
        'chem_form': chem_form,
        'mech_form': mech_form,
        'mtc_form': mtc_form,
        'sncrs': sncrs,
        'blockers': blockers,
        'can_accept': len(blockers) == 0,
    })


@login_required(login_url='master_setup:login')
def raise_sncr(request, batch_id):
    """Raise Supplier Non-Conformance Report (SNCR) for an out-of-spec batch."""
    batch = get_object_or_404(MaterialBatch, pk=batch_id)

    if request.method == 'POST':
        if not check_action_permission(request.user, *ROLES_CAN_RECEIVE_MATERIALS):
            raise PermissionDenied("Access Denied: Your assigned role does not permit issuing Non-Conformance Reports.")
        
        form = SupplierNonConformanceForm(request.POST)
        if form.is_valid():
            sncr = form.save(commit=False)
            sncr.batch = batch
            sncr.raised_by = request.user.get_full_name() or request.user.username
            sncr.save()
            # Update batch status to rejected
            batch.status = 'REJECTED'
            batch.save()
            messages.error(request, f'Supplier Non-Conformance Report "{sncr.report_number}" issued for Heat# {batch.heat_number}. Batch REJECTED.')
            return redirect('material_intake:batch_detail', batch_id=batch.id)
    else:
        # Default report number generator
        import random
        rand_num = random.randint(1000, 9999)
        auth_name = request.user.get_full_name() or request.user.username
        form = SupplierNonConformanceForm(initial={
            'report_number': f'SNCR-2026-{rand_num}',
            'defect_category': 'Metallurgical Chemistry / MTC Non-Conformance',
            'disposition_action': 'Quarantine & Return to Vendor',
            'raised_by': auth_name,
        })

    return render(request, 'material_intake/raise_sncr.html', {
        'batch': batch,
        'form': form,
    })
