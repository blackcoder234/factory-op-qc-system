from django import forms
from .models import MaterialBatch, ChemicalComposition, MechanicalProperties, SupplierNonConformance
from .validators import validate_mtc_document


class MaterialBatchForm(forms.ModelForm):
    class Meta:
        model = MaterialBatch
        fields = ['purchase_order_number', 'heat_number', 'supplier_name', 'part', 'material_grade', 'lot_size', 'unit_of_measure', 'received_date', 'mtc_document', 'dock_inspector', 'notes']
        widgets = {
            'purchase_order_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'placeholder': 'e.g. PO-2026-8812'}),
            'heat_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'placeholder': 'e.g. HT-94821'}),
            'supplier_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'part': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'material_grade': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'placeholder': 'e.g. AISI 4140, SS 316L'}),
            'lot_size': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'received_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'mtc_document': forms.FileInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 focus:outline-none focus:border-emerald-500 text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-emerald-500/10 file:text-emerald-400 hover:file:bg-emerald-500/20'}),
            'dock_inspector': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-emerald-500 text-sm', 'rows': 2}),
        }

    def clean_mtc_document(self):
        doc = self.cleaned_data.get('mtc_document')
        if doc:
            validate_mtc_document(doc)
        return doc


class MtcDocumentUploadForm(forms.ModelForm):
    """Form to upload or replace MTC document from the batch detail verification workspace."""
    class Meta:
        model = MaterialBatch
        fields = ['mtc_document']
        widgets = {
            'mtc_document': forms.FileInput(attrs={
                'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 focus:outline-none focus:border-emerald-500 text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-emerald-500/10 file:text-emerald-400 hover:file:bg-emerald-500/20'
            })
        }

    def clean_mtc_document(self):
        doc = self.cleaned_data.get('mtc_document')
        if not doc:
            raise forms.ValidationError("Please select a valid MTC file to upload.")
        validate_mtc_document(doc)
        return doc


class ChemicalCompositionForm(forms.ModelForm):
    class Meta:
        model = ChemicalComposition
        fields = ['carbon', 'manganese', 'silicon', 'phosphorus', 'sulfur', 'chromium', 'nickel', 'is_composition_ok', 'verified_by']
        widgets = {
            'carbon': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'manganese': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'silicon': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'phosphorus': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'sulfur': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'chromium': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'nickel': forms.NumberInput(attrs={'step': '0.001', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'is_composition_ok': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500'}),
            'verified_by': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_ok = cleaned_data.get('is_composition_ok')
        verified_by = cleaned_data.get('verified_by')
        if is_ok and not verified_by:
            self.add_error('verified_by', 'Name of verifying chemist or metallurgist is required when confirming specification conformance.')
        return cleaned_data


class MechanicalPropertiesForm(forms.ModelForm):
    class Meta:
        model = MechanicalProperties
        fields = ['tensile_strength', 'yield_strength', 'elongation', 'hardness', 'hardness_scale', 'is_properties_ok', 'verified_by']
        widgets = {
            'tensile_strength': forms.NumberInput(attrs={'step': '0.1', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'yield_strength': forms.NumberInput(attrs={'step': '0.1', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'elongation': forms.NumberInput(attrs={'step': '0.1', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'hardness': forms.NumberInput(attrs={'step': '0.1', 'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'hardness_scale': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'is_properties_ok': forms.CheckboxInput(attrs={'class': 'rounded bg-slate-900 border-slate-700 text-emerald-500'}),
            'verified_by': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        is_ok = cleaned_data.get('is_properties_ok')
        verified_by = cleaned_data.get('verified_by')
        if is_ok and not verified_by:
            self.add_error('verified_by', 'Name of verifying quality engineer is required when confirming criteria satisfaction.')
        return cleaned_data


class SupplierNonConformanceForm(forms.ModelForm):
    class Meta:
        model = SupplierNonConformance
        fields = ['report_number', 'severity', 'defect_category', 'disposition_action', 'reason', 'raised_by']
        widgets = {
            'report_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'severity': forms.Select(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'defect_category': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'disposition_action': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
            'reason': forms.Textarea(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm', 'rows': 3}),
            'raised_by': forms.TextInput(attrs={'class': 'w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm'}),
        }

