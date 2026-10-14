from django.contrib import admin
from .models import MaterialBatch, ChemicalComposition, MechanicalProperties, SupplierNonConformance

class ChemicalCompositionInline(admin.StackedInline):
    model = ChemicalComposition
    extra = 0

class MechanicalPropertiesInline(admin.StackedInline):
    model = MechanicalProperties
    extra = 0

class SupplierNonConformanceInline(admin.TabularInline):
    model = SupplierNonConformance
    extra = 0

@admin.register(MaterialBatch)
class MaterialBatchAdmin(admin.ModelAdmin):
    list_display = ('heat_number', 'supplier_name', 'material_grade', 'lot_size', 'unit_of_measure', 'received_date', 'status')
    list_filter = ('status', 'material_grade', 'received_date')
    search_fields = ('heat_number', 'purchase_order_number', 'supplier_name')
    inlines = [ChemicalCompositionInline, MechanicalPropertiesInline, SupplierNonConformanceInline]

@admin.register(ChemicalComposition)
class ChemicalCompositionAdmin(admin.ModelAdmin):
    list_display = ('batch', 'carbon', 'manganese', 'silicon', 'is_composition_ok', 'verified_by')
    search_fields = ('batch__heat_number', 'verified_by')
    list_filter = ('is_composition_ok',)

@admin.register(MechanicalProperties)
class MechanicalPropertiesAdmin(admin.ModelAdmin):
    list_display = ('batch', 'tensile_strength', 'yield_strength', 'elongation', 'hardness', 'is_properties_ok')
    search_fields = ('batch__heat_number',)
    list_filter = ('is_properties_ok',)

@admin.register(SupplierNonConformance)
class SupplierNonConformanceAdmin(admin.ModelAdmin):
    list_display = ('report_number', 'batch', 'severity', 'defect_category', 'raised_by', 'raised_date', 'is_resolved')
    list_filter = ('severity', 'is_resolved', 'raised_date')
    search_fields = ('report_number', 'batch__heat_number', 'reason')
