from django.contrib import admin
from .models import MaintenanceRecord, MachineCalibrationRecord, WorkstationLock

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('machine', 'maintenance_type', 'performed_by', 'performed_date', 'next_due_date', 'status', 'is_overdue')
    list_filter = ('maintenance_type', 'status', 'performed_date')
    search_fields = ('machine__machine_code', 'machine__name', 'performed_by')

@admin.register(MachineCalibrationRecord)
class MachineCalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ('machine', 'calibrated_by', 'calibration_date', 'next_due_date', 'certificate_number', 'result')
    list_filter = ('result', 'calibration_date')
    search_fields = ('machine__machine_code', 'certificate_number', 'calibrated_by')

@admin.register(WorkstationLock)
class WorkstationLockAdmin(admin.ModelAdmin):
    list_display = ('machine', 'is_locked', 'reason_code', 'locked_at', 'locked_by', 'unlocked_at')
    list_filter = ('is_locked', 'reason_code')
    search_fields = ('machine__machine_code', 'reason_details', 'locked_by')
