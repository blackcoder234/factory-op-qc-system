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
            'checklist': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500'}),
            'machine': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500'}),
            'batch_or_serial_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500', 'placeholder': 'e.g. BATCH-2026-001'}),
            'inspector_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500'}),
            'inspection_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500'}),
            'shift': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500'}),
            'remarks': forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-teal-500', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from master_setup.models import Machine
        machines = Machine.objects.select_related('lock_status').all()
        machine_choices = [('', '--------- (Select Workstation)')]
        for m in machines:
            if m.is_locked:
                reason = m.lock_status.get_reason_code_display() if hasattr(m, 'lock_status') and m.lock_status else "PM Overdue"
                machine_choices.append((m.id, f"{m.machine_code} — {m.name} 🔒 [LOCKED: {reason}]"))
            else:
                machine_choices.append((m.id, f"{m.machine_code} — {m.name} ✓ [Operational]"))
        self.fields['machine'].choices = machine_choices

    def clean_machine(self):
        machine = self.cleaned_data.get('machine')
        if machine and machine.is_locked:
            reason = machine.lock_status.get_reason_code_display() if hasattr(machine, 'lock_status') and machine.lock_status else "Preventive Maintenance Overdue"
            raise forms.ValidationError(
                f"Workstation '{machine.machine_code}' is currently LOCKED ({reason})! "
                f"Safety interlock prohibits job assignment until maintenance is cleared and released by a supervisor."
            )
        return machine

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
