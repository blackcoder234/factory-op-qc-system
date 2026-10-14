from django.contrib import admin
from .models import InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading

class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 1

class MeasurementReadingInline(admin.TabularInline):
    model = MeasurementReading
    extra = 0
    readonly_fields = ('result', 'deviation')

@admin.register(InspectionChecklist)
class InspectionChecklistAdmin(admin.ModelAdmin):
    list_display = ('name', 'part', 'checklist_type', 'revision', 'operation_step', 'total_characteristics', 'is_active')
    list_filter = ('checklist_type', 'revision', 'is_active')
    search_fields = ('name', 'part__part_number', 'operation_step')
    inlines = [ChecklistItemInline]

@admin.register(ChecklistItem)
class ChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('checklist', 'sequence_number', 'characteristic_name', 'nominal_value', 'tolerance_plus', 'tolerance_minus', 'measurement_unit', 'is_critical')
    list_filter = ('is_critical', 'measurement_unit')
    search_fields = ('characteristic_name', 'checklist__name')

@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch_or_serial_number', 'checklist', 'machine', 'inspector_name', 'inspection_date', 'shift', 'overall_status')
    list_filter = ('overall_status', 'shift', 'inspection_date')
    search_fields = ('batch_or_serial_number', 'inspector_name', 'checklist__part__part_number')
    inlines = [MeasurementReadingInline]

@admin.register(MeasurementReading)
class MeasurementReadingAdmin(admin.ModelAdmin):
    list_display = ('record', 'checklist_item', 'actual_value', 'deviation', 'result', 'used_gauge')
    list_filter = ('result',)
    search_fields = ('record__batch_or_serial_number', 'checklist_item__characteristic_name')
