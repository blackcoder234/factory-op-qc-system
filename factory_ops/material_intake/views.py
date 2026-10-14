from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import MaterialBatch, ChemicalComposition, MechanicalProperties, SupplierNonConformance
from .forms import MaterialBatchForm, ChemicalCompositionForm, MechanicalPropertiesForm, SupplierNonConformanceForm

def batch_list(request):
    """Module 3: Raw Material Intake Dock Receiving List & Quick Logging."""
    batches = MaterialBatch.objects.select_related('part').all()

    if request.method == 'POST':
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


def batch_detail(request, batch_id):
    """MTC Verification Workspace: Chemical & Mechanical property testing."""
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

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_chemistry':
            chem_form = ChemicalCompositionForm(request.POST, instance=chemistry)
            if chem_form.is_valid():
                c = chem_form.save(commit=False)
                c.verified_at = timezone.now()
                c.save()
                messages.success(request, 'Chemical composition verified and updated!')
                return redirect('material_intake:batch_detail', batch_id=batch.id)

        elif action == 'save_mechanics':
            mech_form = MechanicalPropertiesForm(request.POST, instance=mechanics)
            if mech_form.is_valid():
                m = mech_form.save(commit=False)
                m.verified_at = timezone.now()
                m.save()
                messages.success(request, 'Mechanical properties verified and updated!')
                return redirect('material_intake:batch_detail', batch_id=batch.id)

        elif action == 'accept_batch':
            batch.status = 'ACCEPTED'
            batch.save()
            messages.success(request, f'Batch {batch.heat_number} successfully ACCEPTED and released to production!')
            return redirect('material_intake:batch_detail', batch_id=batch.id)

        elif action == 'quarantine_batch':
            batch.status = 'QUARANTINED'
            batch.save()
            messages.warning(request, f'Batch {batch.heat_number} marked as QUARANTINED in quality hold!')
            return redirect('material_intake:raise_sncr', batch_id=batch.id)

    sncrs = batch.non_conformances.all()

    return render(request, 'material_intake/batch_detail.html', {
        'batch': batch,
        'chemistry': chemistry,
        'mechanics': mechanics,
        'chem_form': chem_form,
        'mech_form': mech_form,
        'sncrs': sncrs,
    })


def raise_sncr(request, batch_id):
    """Raise Supplier Non-Conformance Report (SNCR) for an out-of-spec batch."""
    batch = get_object_or_404(MaterialBatch, pk=batch_id)

    if request.method == 'POST':
        form = SupplierNonConformanceForm(request.POST)
        if form.is_valid():
            sncr = form.save(commit=False)
            sncr.batch = batch
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
        form = SupplierNonConformanceForm(initial={
            'report_number': f'SNCR-2026-{rand_num}',
            'defect_category': 'Metallurgical Chemistry / MTC Non-Conformance',
            'disposition_action': 'Quarantine & Return to Vendor',
            'raised_by': 'Quality Assurance Inspector',
        })

    return render(request, 'material_intake/raise_sncr.html', {
        'batch': batch,
        'form': form,
    })
