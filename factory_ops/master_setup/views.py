from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from datetime import date

from .models import Department, Machine, Part, InspectionGauge
from .forms import DepartmentForm, MachineForm, PartForm, InspectionGaugeForm

from calibration.models import WorkstationLock, MaintenanceRecord
from material_intake.models import MaterialBatch, SupplierNonConformance
from inspection.models import InspectionRecord, InspectionChecklist

def home(request):
    """Apex Precision Dynamics — Public Company & Plant Overview Landing Page."""
    total_machines = Machine.objects.filter(is_active=True).count()
    total_gauges = InspectionGauge.objects.filter(is_active=True).count()
    total_parts = Part.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    total_batches = MaterialBatch.objects.count()
    total_checklists = InspectionChecklist.objects.filter(is_active=True).count()

    return render(request, 'landing.html', {
        'total_machines': total_machines,
        'total_gauges': total_gauges,
        'total_parts': total_parts,
        'total_departments': total_departments,
        'total_batches': total_batches,
        'total_checklists': total_checklists,
    })


def user_login(request):
    """Industrial Plant Terminal Authentication."""
    if request.user.is_authenticated:
        return redirect('master_setup:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            role_title = "Plant Supervisor" if user.is_staff else "Operator"
            messages.success(request, f'Terminal session authenticated. Welcome, {role_title} {user.username}.')
            return redirect('master_setup:dashboard')
        else:
            messages.error(request, 'Access Denied: Invalid employee call-sign or security PIN.')

    return render(request, 'auth/login.html')


def user_logout(request):
    """Terminate terminal session."""
    auth_logout(request)
    messages.info(request, 'Terminal session terminated. You have been logged out.')
    return redirect('master_setup:home')


@login_required(login_url='master_setup:login')
def dashboard(request):
    """Factory Operations Plant Overview Dashboard with live KPIs and alerts."""
    # Key Metrics
    total_departments = Department.objects.filter(is_active=True).count()
    total_machines = Machine.objects.filter(is_active=True).count()
    locked_machines = WorkstationLock.objects.filter(is_locked=True)
    locked_count = locked_machines.count()
    operational_count = total_machines - locked_count

    total_parts = Part.objects.filter(is_active=True).count()
    all_gauges = InspectionGauge.objects.filter(is_active=True)
    total_gauges = all_gauges.count()
    
    # Check overdue gauges
    today = date.today()
    overdue_gauges = [g for g in all_gauges if g.calibration_due_date and g.calibration_due_date < today]

    # Material batches
    total_batches = MaterialBatch.objects.count()
    accepted_batches = MaterialBatch.objects.filter(status='ACCEPTED').count()
    rejected_batches = MaterialBatch.objects.filter(status='REJECTED').count()
    active_sncrs = SupplierNonConformance.objects.filter(is_resolved=False).count()

    # Inspections
    total_inspections = InspectionRecord.objects.count()
    passed_inspections = InspectionRecord.objects.filter(overall_status='PASSED').count()
    failed_inspections = InspectionRecord.objects.filter(overall_status='FAILED').count()
    pass_rate = round((passed_inspections / total_inspections * 100), 1) if total_inspections > 0 else 0

    # Recent inspection activity
    recent_inspections = InspectionRecord.objects.select_related('checklist', 'checklist__part').order_by('-created_at')[:5]

    context = {
        'total_departments': total_departments,
        'total_machines': total_machines,
        'operational_count': operational_count,
        'locked_count': locked_count,
        'locked_machines': locked_machines,
        'total_parts': total_parts,
        'total_gauges': total_gauges,
        'overdue_gauges': overdue_gauges,
        'total_batches': total_batches,
        'accepted_batches': accepted_batches,
        'rejected_batches': rejected_batches,
        'active_sncrs': active_sncrs,
        'total_inspections': total_inspections,
        'passed_inspections': passed_inspections,
        'failed_inspections': failed_inspections,
        'pass_rate': pass_rate,
        'recent_inspections': recent_inspections,
    }
    return render(request, 'master_setup/dashboard.html', context)


def department_list(request):
    """List all factory departments and handle department creation."""
    departments = Department.objects.prefetch_related('machines').all()
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f'Department "{dept.name}" created successfully!')
            return redirect('master_setup:department_list')
    else:
        form = DepartmentForm()

    return render(request, 'master_setup/department_list.html', {
        'departments': departments,
        'form': form,
    })


def machine_list(request):
    """List all machine tools and workstations."""
    machines = Machine.objects.select_related('department').all()
    if request.method == 'POST':
        form = MachineForm(request.POST)
        if form.is_valid():
            m = form.save()
            # Ensure WorkstationLock record exists
            WorkstationLock.objects.get_or_create(machine=m, defaults={'is_locked': False})
            messages.success(request, f'Machine "{m.machine_code} - {m.name}" added successfully!')
            return redirect('master_setup:machine_list')
    else:
        form = MachineForm()

    return render(request, 'master_setup/machine_list.html', {
        'machines': machines,
        'form': form,
    })


def part_list(request):
    """List all manufactured components."""
    parts = Part.objects.all()
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            part = form.save()
            messages.success(request, f'Part "{part.part_number}" added successfully!')
            return redirect('master_setup:part_list')
    else:
        form = PartForm()

    return render(request, 'master_setup/part_list.html', {
        'parts': parts,
        'form': form,
    })


def gauge_list(request):
    """List inspection gauges with calibration due date tracking."""
    gauges = InspectionGauge.objects.all()
    if request.method == 'POST':
        form = InspectionGaugeForm(request.POST)
        if form.is_valid():
            g = form.save()
            messages.success(request, f'Gauge "{g.serial_number}" registered successfully!')
            return redirect('master_setup:gauge_list')
    else:
        form = InspectionGaugeForm()

    return render(request, 'master_setup/gauge_list.html', {
        'gauges': gauges,
        'form': form,
    })
