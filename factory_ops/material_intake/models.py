from django.db import models
from django.utils import timezone
from master_setup.models import Part

class MaterialBatch(models.Model):
    """Raw material intake batch logged at the receiving dock."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Receiving Inspection'),
        ('IN_LAB', 'In Lab Testing'),
        ('ACCEPTED', 'Accepted / Released for Production'),
        ('REJECTED', 'Rejected — SNCR Issued'),
        ('QUARANTINED', 'Quarantined in Quality Hold Area'),
    ]

    purchase_order_number = models.CharField(max_length=50, help_text="PO Reference, e.g. PO-2026-8812")
    heat_number = models.CharField(max_length=50, unique=True, help_text="Steel Mill / Foundry Melt Heat # (e.g. HT-94821)")
    supplier_name = models.CharField(max_length=150, help_text="Material Supplier or Mill Name")
    part = models.ForeignKey(
        Part, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='material_batches', help_text="Intended component"
    )
    material_grade = models.CharField(max_length=60, help_text="e.g. AISI 4140, EN8, SS 304, Ti-6Al-4V")
    lot_size = models.PositiveIntegerField(help_text="Quantity received (pieces / billets / bars)")
    unit_of_measure = models.CharField(max_length=20, default='Pieces', help_text="Pieces, KG, Tonnes, Meters")
    received_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    mtc_document = models.FileField(
        upload_to='mtc_documents/', null=True, blank=True,
        help_text="Original Mill Test Certificate (PDF / Scanned Certificate)"
    )
    dock_inspector = models.CharField(max_length=100, blank=True, help_text="Person who logged the physical delivery")
    notes = models.TextField(blank=True, help_text="Visual inspection notes (packaging, rust, damage)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_date', '-created_at']
        verbose_name = 'Raw Material Batch'
        verbose_name_plural = 'Raw Material Batches'

    def __str__(self):
        return f"Heat# {self.heat_number} ({self.material_grade}) — {self.supplier_name}"


class ChemicalComposition(models.Model):
    """Chemical analysis percentages extracted from the MTC."""
    batch = models.OneToOneField(
        MaterialBatch, on_delete=models.CASCADE, related_name='chemical_composition'
    )
    carbon = models.FloatField(help_text="Carbon % (C)")
    manganese = models.FloatField(help_text="Manganese % (Mn)")
    silicon = models.FloatField(help_text="Silicon % (Si)")
    phosphorus = models.FloatField(null=True, blank=True, default=0.025, help_text="Phosphorus % (P) - max")
    sulfur = models.FloatField(null=True, blank=True, default=0.025, help_text="Sulfur % (S) - max")
    chromium = models.FloatField(null=True, blank=True, default=0.0, help_text="Chromium % (Cr)")
    nickel = models.FloatField(null=True, blank=True, default=0.0, help_text="Nickel % (Ni)")
    
    is_composition_ok = models.BooleanField(
        null=True, blank=True, help_text="True if chemistry conforms to standard specification"
    )
    verified_by = models.CharField(max_length=100, blank=True, help_text="Metallurgist / QC Chemist")
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'MTC Chemical Composition'
        verbose_name_plural = 'MTC Chemical Compositions'

    def __str__(self):
        return f"Chemistry for Heat# {self.batch.heat_number}"


class MechanicalProperties(models.Model):
    """Mechanical test properties verified against material specification."""
    batch = models.OneToOneField(
        MaterialBatch, on_delete=models.CASCADE, related_name='mechanical_properties'
    )
    tensile_strength = models.FloatField(help_text="Ultimate Tensile Strength (UTS) in MPa")
    yield_strength = models.FloatField(help_text="Yield Strength (YS) in MPa")
    elongation = models.FloatField(help_text="Elongation % (A)")
    hardness = models.FloatField(help_text="Hardness value (e.g. HRC or HBW)")
    hardness_scale = models.CharField(max_length=10, default='HRC', choices=[('HRC', 'HRC'), ('HBW', 'HBW'), ('HV', 'HV')])

    is_properties_ok = models.BooleanField(
        null=True, blank=True, help_text="True if mechanical properties satisfy spec sheet"
    )
    verified_by = models.CharField(max_length=100, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'MTC Mechanical Properties'
        verbose_name_plural = 'MTC Mechanical Properties'

    def __str__(self):
        return f"Mechanical Properties for Heat# {self.batch.heat_number}"


class SupplierNonConformance(models.Model):
    """Supplier Non-Conformance Report (SNCR) for rejected or out-of-spec batches."""
    SEVERITY_LEVELS = [
        ('MINOR', 'Minor — Deviation Accepted on Concession'),
        ('MAJOR', 'Major — Rework / Sorting Required'),
        ('CRITICAL', 'Critical — Scrap / Reject Batch & Return to Vendor'),
    ]

    batch = models.ForeignKey(
        MaterialBatch, on_delete=models.CASCADE, related_name='non_conformances'
    )
    report_number = models.CharField(max_length=40, unique=True, help_text="SNCR-2026-XXXX")
    severity = models.CharField(max_length=15, choices=SEVERITY_LEVELS, default='MAJOR')
    defect_category = models.CharField(max_length=100, help_text="e.g. Chemistry Out of Spec, Missing MTC, Surface Cracks")
    disposition_action = models.CharField(max_length=100, default='Quarantine & Return to Supplier')
    reason = models.TextField(help_text="Detailed finding and specification gap")
    raised_by = models.CharField(max_length=100, help_text="Quality Engineer who raised the report")
    raised_date = models.DateField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, help_text="Supplier corrective action (CAPA) or credit note")

    class Meta:
        ordering = ['-raised_date']
        verbose_name = 'Supplier Non-Conformance (SNCR)'
        verbose_name_plural = 'Supplier Non-Conformances (SNCRs)'

    def __str__(self):
        return f"{self.report_number} — {self.batch.heat_number} ({self.get_severity_display()})"
