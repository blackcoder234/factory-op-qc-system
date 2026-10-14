from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading
from .forms import InspectionChecklistForm, ChecklistItemForm, InspectionRecordForm, MeasurementReadingForm
from master_setup.models import InspectionGauge

def checklist_list(request):
    """Module 4: List and manage Inspection Checklist Templates (PDI / In-Process)."""
    checklists = InspectionChecklist.objects.select_related('part').prefetch_related('items').all()

    if request.method == 'POST':
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


def checklist_detail(request, checklist_id):
    """View checklist details and add/edit tolerance characteristic items."""
    checklist = get_object_or_404(InspectionChecklist, pk=checklist_id)
    items = checklist.items.select_related('recommended_gauge').all()

    if request.method == 'POST':
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


def record_list(request):
    """List inspection execution records (Pre-Dispatch Inspections & Batches)."""
    records = InspectionRecord.objects.select_related('checklist', 'checklist__part', 'machine').prefetch_related('readings').all()

    if request.method == 'POST':
        form = InspectionRecordForm(request.POST)
        if form.is_valid():
            rec = form.save()
            # If the selected machine is locked, show warning!
            if rec.machine and rec.machine.is_locked:
                messages.error(request, f'WARNING: Workstation "{rec.machine.machine_code}" is currently LOCKED due to overdue maintenance! Proceeding with inspection under deviation protocol.')
            else:
                messages.success(request, f'Inspection Session #{rec.id} started for Batch {rec.batch_or_serial_number}!')
            return redirect('inspection:record_detail', record_id=rec.id)
    else:
        form = InspectionRecordForm()

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


def record_detail(request, record_id):
    """
    Live Inspection & Measurement Entry Sheet.
    Operator inputs dimensional readings; system validates tolerances and auto-flags Pass/Fail.
    """
    record = get_object_or_404(InspectionRecord, pk=record_id)
    checklist_items = record.checklist.items.select_related('recommended_gauge').all()
    gauges = InspectionGauge.objects.filter(is_active=True)

    # Fetch existing readings keyed by checklist_item_id
    existing_readings = {r.checklist_item_id: r for r in record.readings.select_related('used_gauge').all()}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_reading':
            item_id = request.POST.get('item_id')
            actual_val = request.POST.get('actual_value')
            gauge_id = request.POST.get('gauge_id')
            notes = request.POST.get('notes', '')

            item = get_object_or_404(ChecklistItem, pk=item_id, checklist=record.checklist)
            gauge = InspectionGauge.objects.filter(pk=gauge_id).first() if gauge_id else None

            try:
                val_float = float(actual_val)
                # Check gauge calibration status
                if gauge and gauge.is_calibration_expired:
                    messages.warning(request, f'NOTICE: Measuring gauge "{gauge.serial_number}" calibration is EXPIRED! Calibration alert logged.')

                # Update or create reading
                reading, created = MeasurementReading.objects.get_or_create(
                    record=record,
                    checklist_item=item,
                    defaults={'actual_value': val_float, 'used_gauge': gauge, 'notes': notes}
                )
                if not created:
                    reading.actual_value = val_float
                    reading.used_gauge = gauge
                    reading.notes = notes
                    reading.save() # Triggers auto Pass/Fail calculation in save()

                if reading.result == 'PASS':
                    messages.success(request, f'✓ Item #{item.sequence_number} ({item.characteristic_name}) = {reading.actual_value} mm -> PASS (within {item.lower_limit}–{item.upper_limit} mm)')
                else:
                    messages.error(request, f'✗ Item #{item.sequence_number} ({item.characteristic_name}) = {reading.actual_value} mm -> FAIL OUT OF SPEC (limits: {item.lower_limit}–{item.upper_limit} mm)')

            except (ValueError, TypeError):
                messages.error(request, 'Invalid numerical measurement value entered.')

            return redirect('inspection:record_detail', record_id=record.id)

    # Build item rows with reading data
    item_rows = []
    for item in checklist_items:
        reading = existing_readings.get(item.id)
        item_rows.append({
            'item': item,
            'reading': reading,
        })

    return render(request, 'inspection/record_detail.html', {
        'record': record,
        'item_rows': item_rows,
        'gauges': gauges,
    })
