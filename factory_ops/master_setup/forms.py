from django import forms
from .models import Department, Machine, Part, InspectionGauge

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'location', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'placeholder': 'e.g. MMS-01'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0'}),
        }

class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['department', 'name', 'machine_code', 'machine_type', 'is_active']
        widgets = {
            'department': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'machine_code': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'placeholder': 'e.g. CNC-01'}),
            'machine_type': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'placeholder': 'e.g. 5-Axis Mill'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0'}),
        }

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'name', 'material_spec', 'drawing_number', 'revision', 'description', 'is_active']
        widgets = {
            'part_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'material_spec': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'drawing_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'revision': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0'}),
        }

class InspectionGaugeForm(forms.ModelForm):
    class Meta:
        model = InspectionGauge
        fields = ['serial_number', 'name', 'gauge_type', 'range_min', 'range_max', 'resolution', 'last_calibration_date', 'calibration_due_date', 'location', 'is_active']
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'gauge_type': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'range_min': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'range_max': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'resolution': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'last_calibration_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'calibration_due_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500 focus:ring-0'}),
        }
