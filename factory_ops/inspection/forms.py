from django import forms
from .models import InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading
from master_setup.models import InspectionGauge

class InspectionChecklistForm(forms.ModelForm):
    class Meta:
        model = InspectionChecklist
        fields = ['name', 'part', 'checklist_type', 'revision', 'operation_step', 'blueprint_reference', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'part': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'checklist_type': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'revision': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'operation_step': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'blueprint_reference': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500'}),
        }

class ChecklistItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistItem
        fields = ['sequence_number', 'characteristic_name', 'nominal_value', 'tolerance_plus', 'tolerance_minus', 'measurement_unit', 'recommended_gauge', 'is_critical']
        widgets = {
            'sequence_number': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'characteristic_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm', 'placeholder': 'e.g. Bore Diameter'}),
            'nominal_value': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'tolerance_plus': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'tolerance_minus': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'measurement_unit': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'recommended_gauge': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'is_critical': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-rose-500'}),
        }

class InspectionRecordForm(forms.ModelForm):
    class Meta:
        model = InspectionRecord
        fields = ['checklist', 'machine', 'batch_or_serial_number', 'inspector_name', 'inspection_date', 'shift', 'remarks']
        widgets = {
            'checklist': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'machine': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'batch_or_serial_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm', 'placeholder': 'e.g. BATCH-2026-001'}),
            'inspector_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'shift': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'remarks': forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm', 'rows': 2}),
        }

class MeasurementReadingForm(forms.ModelForm):
    class Meta:
        model = MeasurementReading
        fields = ['checklist_item', 'actual_value', 'used_gauge', 'notes']
        widgets = {
            'checklist_item': forms.HiddenInput(),
            'actual_value': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'used_gauge': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'notes': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm', 'placeholder': 'Optional observation'}),
        }
