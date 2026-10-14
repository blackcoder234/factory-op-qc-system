from django.db import models
from django.utils import timezone
from master_setup.models import Part, Machine, InspectionGauge

class InspectionChecklist(models.Model):
    """Template checklist defining inspection criteria for a manufactured component."""
    CHECKLIST_TYPES = [
        ('PDI', 'Pre-Dispatch Inspection (PDI)'),
        ('IN_PROCESS', 'In-Process Quality Inspection'),
        ('FIRST_PIECE', 'First Piece / Setup Inspection (FAI)'),
        ('FINAL', 'Final Quality Clearance'),
    ]

    name = models.CharField(max_length=150, help_text="e.g., Turbine Flange Final PDI Checklist")
    part = models.ForeignKey(
        Part, on_delete=models.CASCADE, related_name='checklists'
    )
    checklist_type = models.CharField(max_length=20, choices=CHECKLIST_TYPES, default='PDI')
    revision = models.CharField(max_length=10, default='A', help_text="Must match blueprint revision")
    operation_step = models.CharField(max_length=100, default='OP-50 Final Machining', help_text="e.g. OP-20 Turning, OP-40 Grinding")
    blueprint_reference = models.CharField(max_length=100, blank=True, help_text="Drawing title & section reference")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['part', 'name']
        verbose_name = 'Inspection Checklist Template'
        verbose_name_plural = 'Inspection Checklist Templates'

    def __str__(self):
        return f"{self.name} (Rev {self.revision}) — {self.part.part_number}"

    @property
    def total_characteristics(self):
        return self.items.count()


class ChecklistItem(models.Model):
    """A single dimensional or visual inspection checkpoint with tolerance limits."""
    checklist = models.ForeignKey(
        InspectionChecklist, on_delete=models.CASCADE, related_name='items'
    )
    sequence_number = models.PositiveIntegerField(help_text="Step order (e.g. 1, 2, 3)")
    characteristic_name = models.CharField(
        max_length=150, help_text="e.g. Bore Inner Diameter, Flange Thickness, PCD Runout"
    )
    nominal_value = models.FloatField(help_text="Target nominal dimension in mm")
    tolerance_plus = models.FloatField(default=0.02, help_text="Upper tolerance offset (e.g. 0.02)")
    tolerance_minus = models.FloatField(default=0.02, help_text="Lower tolerance offset (e.g. 0.02)")
    measurement_unit = models.CharField(max_length=20, default='mm')
    recommended_gauge = models.ForeignKey(
        InspectionGauge, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='checklist_items', help_text="Recommended calibrated instrument"
    )
    is_critical = models.BooleanField(
        default=False, help_text="Critical Quality Characteristic (CTQ) — zero tolerance for failure"
    )

    class Meta:
        ordering = ['checklist', 'sequence_number']
        unique_together = ['checklist', 'sequence_number']
        verbose_name = 'Checklist Inspection Item'
        verbose_name_plural = 'Checklist Inspection Items'

    @property
    def upper_limit(self):
        return round(self.nominal_value + self.tolerance_plus, 4)

    @property
    def lower_limit(self):
        return round(self.nominal_value - self.tolerance_minus, 4)

    def __str__(self):
        return f"#{self.sequence_number}: {self.characteristic_name} [{self.nominal_value} +{self.tolerance_plus}/-{self.tolerance_minus} {self.measurement_unit}]"


class InspectionRecord(models.Model):
    """An actual inspection session conducted for a production batch or component."""
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress / Readings Incomplete'),
        ('PASSED', 'Passed — All Dimensions In Tolerance'),
        ('FAILED', 'Failed — Out-of-Tolerance Detected'),
        ('ON_HOLD', 'On Hold — Deviation Review Pending'),
    ]

    checklist = models.ForeignKey(
        InspectionChecklist, on_delete=models.CASCADE, related_name='records'
    )
    machine = models.ForeignKey(
        Machine, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='inspections', help_text="Workstation where part was machined"
    )
    batch_or_serial_number = models.CharField(max_length=60, help_text="Batch Lot# or Serial#")
    inspector_name = models.CharField(max_length=100, help_text="Operator or QC Inspector name")
    inspection_date = models.DateField(default=timezone.now)
    shift = models.CharField(
        max_length=20, default='Shift A (Morning)',
        choices=[
            ('Shift A (Morning)', 'Shift A (Morning)'),
            ('Shift B (Afternoon)', 'Shift B (Afternoon)'),
            ('Shift C (Night)', 'Shift C (Night)'),
        ]
    )
    overall_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    remarks = models.TextField(blank=True, help_text="Inspector observations or disposition comments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-inspection_date', '-created_at']
        verbose_name = 'Inspection Record'
        verbose_name_plural = 'Inspection Records'

    def __str__(self):
        return f"Record #{self.id} [{self.batch_or_serial_number}] — {self.checklist.part.part_number}"

    def update_overall_status(self):
        """Auto-evaluates overall record status based on all readings."""
        readings = self.readings.all()
        total_items = self.checklist.items.count()

        if readings.count() == 0 or readings.count() < total_items:
            self.overall_status = 'IN_PROGRESS'
        elif any(r.result == 'FAIL' for r in readings):
            self.overall_status = 'FAILED'
        else:
            self.overall_status = 'PASSED'
        self.save()


class MeasurementReading(models.Model):
    """
    Individual measurement reading recorded by the inspector.
    Calculates PASS / FAIL dynamically based on checklist item tolerances upon save.
    """
    RESULT_CHOICES = [
        ('PASS', 'Pass'),
        ('FAIL', 'Fail (Out of Spec)'),
        ('PENDING', 'Pending Measurement'),
    ]

    record = models.ForeignKey(
        InspectionRecord, on_delete=models.CASCADE, related_name='readings'
    )
    checklist_item = models.ForeignKey(
        ChecklistItem, on_delete=models.CASCADE, related_name='readings'
    )
    actual_value = models.FloatField(help_text="Actual measured value from instrument")
    deviation = models.FloatField(default=0.0, help_text="Actual minus Nominal")
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default='PENDING')
    used_gauge = models.ForeignKey(
        InspectionGauge, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Gauge serial number used for this reading"
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ['record', 'checklist_item']
        verbose_name = 'Measurement Reading'
        verbose_name_plural = 'Measurement Readings'

    def save(self, *args, **kwargs):
        """
        Auto-calculate Pass/Fail tolerance check right before saving.
        Guarantees business logic integrity at the database model level.
        """
        item = self.checklist_item
        lower = item.lower_limit
        upper = item.upper_limit
        
        # Calculate deviation
        self.deviation = round(self.actual_value - item.nominal_value, 4)

        # Check tolerance limits
        if lower <= round(self.actual_value, 4) <= upper:
            self.result = 'PASS'
        else:
            self.result = 'FAIL'

        super().save(*args, **kwargs)
        # Notify parent record to re-evaluate overall pass/fail status
        self.record.update_overall_status()

    def __str__(self):
        return f"{self.checklist_item.characteristic_name}: {self.actual_value} -> {self.result}"
