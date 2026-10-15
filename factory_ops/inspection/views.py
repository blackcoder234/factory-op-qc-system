from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import (
    InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading,
    ProductionOperation, DispatchClearance
)
from .forms import (
    InspectionChecklistForm,
    ChecklistItemForm,
    InspectionRecordForm,
    MeasurementReadingForm,
    InspectionReviewForm,
    DispatchClearanceForm,
)
from master_setup.models import InspectionGauge

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from master_setup.rbac import (
    check_action_permission,
    ROLES_CAN_CREATE_CHECKLIST,
    ROLES_CAN_START_INSPECTION,
    ROLES_CAN_ENTER_READINGS,
    ROLES_CAN_APPROVE_INSPECTION,
    ROLES_CAN_APPROVE_DISPATCH,
    ROLES_CAN_RECEIVE_MATERIALS,
)


@login_required(login_url='master_setup:login')
def checklist_list(request):
    """Module 4: List and manage Inspection Checklist Templates (PDI / In-Process)."""
    checklists = InspectionChecklist.objects.select_related('part').prefetch_related('items').all()

    if request.method == 'POST':
        if not check_action_permission(request.user, *ROLES_CAN_CREATE_CHECKLIST):
            raise PermissionDenied("Access Denied: Only Quality Engineers or Quality Managers can create inspection checklist templates.")

        form = InspectionChecklistForm(request.POST)
        if form.is_valid():
            cl = form.save()
            messages.success(request, f'Checklist "{cl.name}" created! Now add measurement items below.')
            return redirect('inspection:checklist_detail', checklist_id=cl.id)
    else:
        form = InspectionChecklistForm()

    return render(request, 'inspection/checklist_list.html', {
        'checklists': checklists,
        'form': form,
    })


@login_required(login_url='master_setup:login')
def checklist_detail(request, checklist_id):
    """View checklist details and add/edit tolerance characteristic items."""
    checklist = get_object_or_404(InspectionChecklist, pk=checklist_id)
    items = checklist.items.select_related('recommended_gauge').all()

    if request.method == 'POST':
        if not check_action_permission(request.user, *ROLES_CAN_CREATE_CHECKLIST):
            raise PermissionDenied("Access Denied: Only Quality Engineers or Quality Managers can edit checklist characteristics.")

        item_form = ChecklistItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.checklist = checklist
            item.save()
            messages.success(request, f'Characteristic "#{item.sequence_number} {item.characteristic_name}" added to template!')
            return redirect('inspection:checklist_detail', checklist_id=checklist.id)
    else:
        next_seq = items.count() + 1
        item_form = ChecklistItemForm(initial={'sequence_number': next_seq, 'tolerance_plus': 0.02, 'tolerance_minus': 0.02, 'measurement_unit': 'mm'})

    return render(request, 'inspection/checklist_detail.html', {
        'checklist': checklist,
        'items': items,
        'item_form': item_form,
    })


@login_required(login_url='master_setup:login')
def record_list(request):
    """List inspection execution records (Pre-Dispatch Inspections & Batches)."""
    records = InspectionRecord.objects.select_related('checklist', 'checklist__part', 'machine').prefetch_related('readings').all()

    if request.method == 'POST':
        if not check_action_permission(request.user, *ROLES_CAN_START_INSPECTION):
            raise PermissionDenied("Access Denied: Your assigned role does not permit starting inspection sessions.")

        form = InspectionRecordForm(request.POST)
        if form.is_valid():
            rec = form.save()
            messages.success(request, f'Inspection Session #{rec.id} started for Batch {rec.batch_or_serial_number}!')
            return redirect('inspection:record_detail', record_id=rec.id)
        else:
            messages.error(request, 'Cannot start inspection session: Workstation is locked or input is invalid. Please review errors below.')
    else:
        auth_name = request.user.get_full_name() or request.user.username
        form = InspectionRecordForm(initial={'inspector_name': auth_name})

    passed_count = records.filter(overall_status='PASSED').count()
    failed_count = records.filter(overall_status='FAILED').count()
    in_progress_count = records.filter(overall_status='IN_PROGRESS').count()

    return render(request, 'inspection/record_list.html', {
        'records': records,
        'form': form,
        'passed_count': passed_count,
        'failed_count': failed_count,
        'in_progress_count': in_progress_count,
    })


@login_required(login_url='master_setup:login')
def record_detail(request, record_id):
    """
    Live Inspection & Measurement Entry Sheet.
    Operator inputs dimensional readings; system validates tolerances and auto-flags Pass/Fail.
    Enforces calibration validity and supervisor approval sign-off.
    """
    record = get_object_or_404(InspectionRecord, pk=record_id)
    checklist_items = record.checklist.items.select_related('recommended_gauge').all()
    gauges = InspectionGauge.objects.filter(is_active=True)

    # Fetch existing readings keyed by checklist_item_id
    existing_readings = {r.checklist_item_id: r for r in record.readings.select_related('used_gauge').all()}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_reading':
            if not check_action_permission(request.user, *ROLES_CAN_ENTER_READINGS):
                raise PermissionDenied("Access Denied: Only QA Floor Inspectors, Quality Engineers, or Quality Managers can record measurement readings.")

            if record.review_status == 'APPROVED':
                messages.error(request, "This inspection session has already been APPROVED and locked by supervisor. Measurement readings cannot be modified.")
                return redirect('inspection:record_detail', record_id=record.id)

            item_id = request.POST.get('item_id')
            gauge_id = request.POST.get('gauge_id')
            notes = request.POST.get('notes', '')

            # Validate with MeasurementReadingForm
            form_payload = {
                'checklist_item': item_id,
                'actual_value': request.POST.get('actual_value'),
                'used_gauge': gauge_id if gauge_id else '',
                'notes': notes,
            }
            form = MeasurementReadingForm(data=form_payload)

            if form.is_valid():
                item = form.cleaned_data['checklist_item']
                val_float = form.cleaned_data['actual_value']
                gauge = form.cleaned_data.get('used_gauge')

                # Ensure item belongs to record checklist
                if item.checklist_id != record.checklist_id:
                    messages.error(request, "Invalid characteristic checkpoint for this session.")
                    return redirect('inspection:record_detail', record_id=record.id)

                try:
                    reading, created = MeasurementReading.objects.get_or_create(
                        record=record,
                        checklist_item=item,
                        defaults={'actual_value': val_float, 'used_gauge': gauge, 'notes': notes}
                    )
                    if not created:
                        reading.actual_value = val_float
                        reading.used_gauge = gauge
                        reading.notes = notes
                        reading.save()
                except Exception as ex:
                    messages.error(request, f"Measurement Entry Error: {ex}")
                    return redirect('inspection:record_detail', record_id=record.id)

                if reading.result == 'PASS':
                    messages.success(request, f'✓ Item #{item.sequence_number} ({item.characteristic_name}) = {reading.actual_value} mm -> PASS (within {item.lower_limit}–{item.upper_limit} mm)')
                else:
                    messages.error(request, f'✗ Item #{item.sequence_number} ({item.characteristic_name}) = {reading.actual_value} mm -> FAIL OUT OF SPEC (limits: {item.lower_limit}–{item.upper_limit} mm)')
            else:
                for field, errs in form.errors.items():
                    for err in errs:
                        messages.error(request, f"Measurement Entry Error: {err}")

            return redirect('inspection:record_detail', record_id=record.id)

        elif action == 'approve_record':
            if not check_action_permission(request.user, *ROLES_CAN_APPROVE_INSPECTION):
                raise PermissionDenied("Access Denied: Only Shift Supervisors or Quality Managers have authority to sign off and approve inspection sessions.")

            blockers = record.get_approval_blockers()
            if blockers:
                for b in blockers:
                    messages.error(request, f"Approval Blocked: {b}")
                return redirect('inspection:record_detail', record_id=record.id)

            record.review_status = 'APPROVED'
            record.reviewed_by = request.user.get_full_name() or request.user.username
            record.reviewed_at = timezone.now()
            record.review_notes = request.POST.get('review_notes', '')
            record.full_clean()
            record.save()
            messages.success(request, f'Inspection Session #{record.id} successfully reviewed and APPROVED by {record.reviewed_by}!')
            return redirect('inspection:record_detail', record_id=record.id)

        elif action == 'reject_record':
            if not check_action_permission(request.user, *ROLES_CAN_APPROVE_INSPECTION):
                raise PermissionDenied("Access Denied: Only Shift Supervisors or Quality Managers have authority to reject inspection sessions.")

            record.review_status = 'REJECTED'
            record.overall_status = 'FAILED'
            record.reviewed_by = request.user.get_full_name() or request.user.username
            record.reviewed_at = timezone.now()
            record.review_notes = request.POST.get('review_notes', '')
            record.save()
            messages.warning(request, f'Inspection Session #{record.id} marked as REJECTED by {record.reviewed_by}.')
            return redirect('inspection:record_detail', record_id=record.id)

    # Build item rows with reading data
    item_rows = []
    for item in checklist_items:
        reading = existing_readings.get(item.id)
        item_rows.append({
            'item': item,
            'reading': reading,
        })

    blockers = record.get_approval_blockers()
    can_user_approve = check_action_permission(request.user, *ROLES_CAN_APPROVE_INSPECTION)

    return render(request, 'inspection/record_detail.html', {
        'record': record,
        'item_rows': item_rows,
        'gauges': gauges,
        'review_form': InspectionReviewForm(instance=record),
        'blockers': blockers,
        'can_approve': len(blockers) == 0,
        'can_user_approve': can_user_approve,
    })


@login_required(login_url='master_setup:login')
def dispatch_list(request):
    """
    List Dispatch Clearance requests and initiate new clearance verification orders.
    Zero-escape gate: releases finished goods only when raw materials, operations,
    process hold durations, and PDI inspections are fully satisfied.
    """
    clearances = DispatchClearance.objects.select_related(
        'part', 'material_batch', 'inspection_record', 'created_by', 'cleared_by'
    ).all()

    if request.method == 'POST':
        if not check_action_permission(request.user, *ROLES_CAN_RECEIVE_MATERIALS):
            raise PermissionDenied("Access Denied: Your assigned role does not permit creating dispatch clearance orders.")

        form = DispatchClearanceForm(request.POST)
        if form.is_valid():
            dispatch_order = form.save(commit=False)
            dispatch_order.created_by = request.user
            dispatch_order.save()
            messages.success(
                request,
                f"Dispatch Order '{dispatch_order.dispatch_order_number}' initialized! Run quality audit gate verification below."
            )
            return redirect('inspection:dispatch_detail', dispatch_id=dispatch_order.id)
        else:
            messages.error(request, "Failed to create dispatch clearance order. Please check form errors below.")
    else:
        form = DispatchClearanceForm()

    cleared_count = clearances.filter(status='CLEARED').count()
    pending_count = clearances.filter(status='PENDING_AUDIT').count()
    rejected_count = clearances.filter(status='REJECTED').count()

    return render(request, 'inspection/dispatch_list.html', {
        'clearances': clearances,
        'form': form,
        'cleared_count': cleared_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
    })


@login_required(login_url='master_setup:login')
def dispatch_detail(request, dispatch_id):
    """
    Zero-Escape Dispatch Quality Gate Audit & Release Screen.
    Performs server-side cross-module validation against:
    1. Material Intake Batch status & unresolved SNCRs
    2. Shopfloor Production Operations & mandatory hold periods
    3. Final PDI Inspection record pass status & supervisor sign-off
    Enforces atomic state transitions and concurrency locks.
    """
    dispatch = get_object_or_404(
        DispatchClearance.objects.select_related(
            'part', 'material_batch',
            'inspection_record', 'inspection_record__checklist',
            'created_by', 'cleared_by'
        ),
        pk=dispatch_id
    )

    operations = ProductionOperation.objects.filter(
        batch_number=dispatch.batch_or_serial_number
    ).select_related('machine', 'completed_by')

    can_user_authorize = check_action_permission(request.user, *ROLES_CAN_APPROVE_DISPATCH)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'clear_dispatch':
            if not can_user_authorize:
                raise PermissionDenied(
                    "Access Denied: Only Plant / General Managers or Quality Managers have authority to clear and release dispatches."
                )

            with transaction.atomic():
                locked_dispatch = DispatchClearance.objects.select_for_update().get(pk=dispatch.id)
                blockers = locked_dispatch.get_clearance_blockers()
                if blockers:
                    for b in blockers:
                        messages.error(request, f"Dispatch Release Prohibited: {b}")
                    return redirect('inspection:dispatch_detail', dispatch_id=locked_dispatch.id)

                locked_dispatch.status = 'CLEARED'
                locked_dispatch.cleared_by = request.user
                locked_dispatch.cleared_at = timezone.now()
                notes = request.POST.get('clearance_notes', '').strip()
                if notes:
                    locked_dispatch.clearance_notes = notes
                locked_dispatch.save()

                messages.success(
                    request,
                    f"✓ DISPATCH RELEASE AUTHORIZED: Order {locked_dispatch.dispatch_order_number} released for shipment to {locked_dispatch.destination}!"
                )
                return redirect('inspection:dispatch_detail', dispatch_id=locked_dispatch.id)

        elif action == 'reject_dispatch':
            if not can_user_authorize:
                raise PermissionDenied(
                    "Access Denied: Only Plant / General Managers or Quality Managers have authority to reject or place quality holds on dispatches."
                )

            with transaction.atomic():
                locked_dispatch = DispatchClearance.objects.select_for_update().get(pk=dispatch.id)
                locked_dispatch.status = 'REJECTED'
                locked_dispatch.cleared_by = request.user
                locked_dispatch.cleared_at = timezone.now()
                notes = request.POST.get('clearance_notes', '').strip()
                if notes:
                    locked_dispatch.clearance_notes = notes
                locked_dispatch.save()

                messages.warning(
                    request,
                    f"⚠ DISPATCH ORDER REJECTED: Order {locked_dispatch.dispatch_order_number} has been placed on Quality Quarantine / Hold."
                )
                return redirect('inspection:dispatch_detail', dispatch_id=locked_dispatch.id)

    blockers = dispatch.get_clearance_blockers()
    can_be_cleared = len(blockers) == 0 and dispatch.status != 'CLEARED'

    # Prerequisite status breakdown for visual checklist cards
    mat_batch = dispatch.material_batch
    mat_ok = bool(mat_batch and mat_batch.status == 'ACCEPTED' and not mat_batch.non_conformances.filter(is_resolved=False).exists())
    
    ops_exist = operations.exists()
    ops_complete = ops_exist and not operations.exclude(status='COMPLETED').exists()
    holds_elapsed = ops_exist and all(op.is_hold_elapsed for op in operations)

    pdi = dispatch.inspection_record
    pdi_ok = bool(pdi and pdi.overall_status == 'PASSED' and pdi.review_status == 'APPROVED')

    return render(request, 'inspection/dispatch_detail.html', {
        'dispatch': dispatch,
        'operations': operations,
        'blockers': blockers,
        'can_be_cleared': can_be_cleared,
        'can_user_authorize': can_user_authorize,
        'mat_ok': mat_ok,
        'ops_exist': ops_exist,
        'ops_complete': ops_complete,
        'holds_elapsed': holds_elapsed,
        'pdi_ok': pdi_ok,
    })
