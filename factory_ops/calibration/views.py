from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date

from .models import WorkstationLock, MaintenanceRecord, MachineCalibrationRecord
from .forms import MaintenanceRecordForm, WorkstationLockToggleForm
from master_setup.models import Machine

def machine_lock_list(request):
    """Module 2: Machine Calibration & Workstation Lock status board."""
    # Ensure all machines have a WorkstationLock object
    machines = Machine.objects.select_related('department').all()
    for m in machines:
        WorkstationLock.objects.get_or_create(machine=m, defaults={'is_locked': False})

    locks = WorkstationLock.objects.select_related('machine', 'machine__department').all()
    recent_maintenance = MaintenanceRecord.objects.select_related('machine').order_by('-performed_date')[:6]

    locked_count = locks.filter(is_locked=True).count()
    operational_count = locks.filter(is_locked=False).count()

    return render(request, 'calibration/machine_lock_list.html', {
        'locks': locks,
        'recent_maintenance': recent_maintenance,
        'locked_count': locked_count,
        'operational_count': operational_count,
    })


def toggle_lock(request, machine_id):
    """Enforce or release a workstation lock."""
    machine = get_object_or_404(Machine, pk=machine_id)
    lock_obj, _ = WorkstationLock.objects.get_or_create(machine=machine)

    if request.method == 'POST':
        form = WorkstationLockToggleForm(request.POST)
        if form.is_valid():
            supervisor = form.cleaned_data['supervisor_name']
            reason_code = form.cleaned_data['reason_code']
            details = form.cleaned_data['reason_details']

            if lock_obj.is_locked:
                lock_obj.release_lock(user_name=supervisor)
                messages.success(request, f'Workstation "{machine.machine_code}" unlocked by {supervisor}. Status returned to OPERATIONAL.')
            else:
                lock_obj.trigger_lock(reason_code=reason_code, reason_details=details, user_name=supervisor)
                messages.warning(request, f'Workstation "{machine.machine_code}" LOCKED by {supervisor}. Job selection is now disabled!')

            return redirect('calibration:machine_lock_list')
    else:
        form = WorkstationLockToggleForm(initial={
            'reason_code': 'MANUAL_SUPERVISOR' if not lock_obj.is_locked else lock_obj.reason_code,
            'reason_details': 'Supervisor quality clearance check.' if lock_obj.is_locked else 'Precautionary lock for calibration inspection.',
            'supervisor_name': 'Supervisor QA Lead',
        })

    return render(request, 'calibration/toggle_lock.html', {
        'machine': machine,
        'lock_obj': lock_obj,
        'form': form,
    })


def maintenance_log(request):
    """Log and review preventive maintenance records."""
    records = MaintenanceRecord.objects.select_related('machine').all()
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            rec = form.save()
            # If PM failed, auto-lock workstation!
            if rec.status == 'FAIL':
                lock_obj, _ = WorkstationLock.objects.get_or_create(machine=rec.machine)
                lock_obj.trigger_lock(
                    reason_code='SAFETY_FAILED',
                    reason_details=f'Maintenance failed: {rec.checklist_notes}',
                    user_name=rec.performed_by
                )
                messages.error(request, f'Maintenance FAILED! Workstation "{rec.machine.machine_code}" has been AUTOMATICALLY LOCKED.')
            else:
                messages.success(request, f'Maintenance log recorded for {rec.machine.machine_code}. Status: {rec.get_status_display()}')
            return redirect('calibration:maintenance_log')
    else:
        form = MaintenanceRecordForm()

    return render(request, 'calibration/maintenance_log.html', {
        'records': records,
        'form': form,
    })
