from django.contrib import admin
from .models import Department, Machine, Part, InspectionGauge

admin.site.site_header = "FactoryOps QC — Enterprise Administration"
admin.site.site_title = "FactoryOps QC Admin"
admin.site.index_title = "Quality Control & Shopfloor Management"

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'location', 'total_machines', 'active_machines', 'is_active')
    search_fields = ('name', 'code', 'location')
    list_filter = ('is_active',)

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_code', 'name', 'department', 'machine_type', 'is_active', 'is_locked')
    search_fields = ('machine_code', 'name')
    list_filter = ('department', 'machine_type', 'is_active')

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'name', 'material_spec', 'drawing_number', 'revision', 'is_active')
    search_fields = ('part_number', 'name', 'drawing_number')
    list_filter = ('revision', 'is_active')

@admin.register(InspectionGauge)
class InspectionGaugeAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'name', 'gauge_type', 'range_min', 'range_max', 'calibration_due_date', 'is_calibration_expired', 'is_active')
    search_fields = ('serial_number', 'name', 'location')
    list_filter = ('gauge_type', 'is_active')
