from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from master_setup.models import Part, Machine, InspectionGauge
from .validators import validate_measurement_value

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

    REVIEW_STATUS_CHOICES = [
        ('PENDING', 'Pending Supervisor Review'),
        ('APPROVED', 'Approved by Supervisor'),
        ('REJECTED', 'Rejected by Supervisor'),
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
    
    # Supervisor Review & Approval fields
    reviewed_by = models.CharField(max_length=100, blank=True, help_text="Supervisor or Quality Manager who reviewed session")
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of supervisor sign-off")
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default='PENDING')
    review_notes = models.TextField(blank=True, help_text="Supervisor sign-off notes or disposition")
    
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

        if total_items == 0 or readings.count() < total_items:
            self.overall_status = 'IN_PROGRESS'
        elif any(r.result == 'FAIL' for r in readings):
            self.overall_status = 'FAILED'
        else:
            self.overall_status = 'PASSED'
        self.save()

    def get_approval_blockers(self):
        """
        Returns all blocking conditions preventing this inspection session from supervisor sign-off.
        Returns an empty list if eligible for approval.
        """
        blockers = []
        total_items = self.checklist.items.count()
        readings_count = self.readings.count()

        if total_items == 0:
            blockers.append("Checklist template has no characteristic inspection items defined.")
        elif readings_count < total_items:
            blockers.append(f"Incomplete inspection: Only {readings_count} of {total_items} characteristics recorded.")

        failing = self.readings.filter(result='FAIL')
        if failing.exists():
            blockers.append(f"{failing.count()} characteristic(s) failed out-of-tolerance specification.")

        if self.overall_status != 'PASSED':
            blockers.append(f"Inspection session overall status is '{self.get_overall_status_display()}'. Only PASSED sessions can be approved.")

        return blockers

    @property
    def can_be_approved(self):
        return len(self.get_approval_blockers()) == 0

    @property
    def is_approved(self):
        return self.review_status == 'APPROVED'

    @property
    def total_items_count(self):
        return self.checklist.items.count()

    @property
    def completed_readings_count(self):
        return self.readings.count()

    @property
    def passed_readings_count(self):
        return self.readings.filter(result='PASS').count()

    @property
    def failed_readings_count(self):
        return self.readings.filter(result='FAIL').count()


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
    actual_value = models.FloatField(
        validators=[validate_measurement_value],
        help_text="Actual measured value from instrument"
    )
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


class ProductionOperation(models.Model):
    """
    Shopfloor manufacturing operation step tracking for components/batches.
    Supports sequence ordering and mandatory process hold periods (e.g. stress relief cooling).
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Setup'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    batch_number = models.CharField(max_length=60, help_text="Component batch or serial number")
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='production_operations')
    operation_name = models.CharField(max_length=120, help_text="e.g. OP-10 Turning, OP-30 Heat Treat & Quench")
    sequence_number = models.PositiveIntegerField(default=10)
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True, related_name='production_operations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Hold requirements (demonstration / illustrative process hold period)
    hold_duration_hours = models.FloatField(default=0.0, help_text="Illustrative process hold / stress relief duration in hours")
    hold_started_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when hold period began")
    
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_operations')
    completion_notes = models.TextField(blank=True, help_text="Operator notes or machine run log")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['batch_number', 'sequence_number']
        unique_together = ['batch_number', 'sequence_number']
        verbose_name = 'Production Operation'
        verbose_name_plural = 'Production Operations'

    def __str__(self):
        return f"{self.batch_number} - OP {self.sequence_number}: {self.operation_name} ({self.get_status_display()})"

    @property
    def is_hold_elapsed(self):
        """Returns True if required hold period has elapsed using server-side time."""
        if not self.hold_duration_hours or self.hold_duration_hours <= 0:
            return True
        if not self.hold_started_at:
            return False
        hold_target = self.hold_started_at + timezone.timedelta(hours=self.hold_duration_hours)
        return timezone.now() >= hold_target

    @property
    def remaining_hold_seconds(self):
        if not self.hold_duration_hours or not self.hold_started_at:
            return 0
        hold_target = self.hold_started_at + timezone.timedelta(hours=self.hold_duration_hours)
        diff = (hold_target - timezone.now()).total_seconds()
        return max(0, int(diff))

    @property
    def remaining_hold_minutes(self):
        return self.remaining_hold_seconds // 60


class DispatchClearance(models.Model):
    """
    Database-backed zero-escape dispatch clearance gate.
    Finished parts cannot be released for shipment without verified digital sign-offs
    across raw material acceptance, completed production operations, elapsed hold periods,
    and approved final PDI inspection records.
    """
    STATUS_CHOICES = [
        ('PENDING_AUDIT', 'Pending Quality Audit Gate'),
        ('CLEARED', 'Cleared & Released for Shipment'),
        ('REJECTED', 'Clearance Denied / Quality Hold'),
    ]

    dispatch_order_number = models.CharField(max_length=50, unique=True, help_text="e.g. DSP-2026-0042")
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='dispatch_clearances')
    batch_or_serial_number = models.CharField(max_length=60, help_text="Finished production batch / lot number")
    material_batch = models.ForeignKey(
        'material_intake.MaterialBatch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dispatch_clearances', help_text="Traceable raw material intake batch"
    )
    inspection_record = models.ForeignKey(
        InspectionRecord, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dispatch_clearances', help_text="Approved Pre-Dispatch Inspection (PDI) session"
    )
    quantity = models.PositiveIntegerField(default=1, help_text="Quantity authorized for release")
    destination = models.CharField(max_length=150, help_text="Customer / Distribution Center Destination")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_AUDIT')
    
    # Audit trail fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_dispatches')
    created_at = models.DateTimeField(auto_now_add=True)
    cleared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cleared_dispatches')
    cleared_at = models.DateTimeField(null=True, blank=True)
    clearance_notes = models.TextField(blank=True, help_text="Clearance remarks, shipping bill of lading, or hold reason")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dispatch Clearance'
        verbose_name_plural = 'Dispatch Clearances'

    def __str__(self):
        return f"{self.dispatch_order_number} — {self.part.part_number} [{self.get_status_display()}]"

    def get_clearance_blockers(self):
        """
        Server-side validation gate verifying all Section 11.3 dispatch prerequisites.
        Returns an empty list if eligible for dispatch release.
        """
        blockers = []

        # 1. Material batch validation
        if not self.material_batch:
            blockers.append("Material Traceability Gap: No inward raw material batch linked to this clearance order.")
        else:
            if self.material_batch.status != 'ACCEPTED':
                blockers.append(
                    f"Raw material batch '{self.material_batch.heat_number}' is '{self.material_batch.get_status_display()}'. "
                    f"Material must be in ACCEPTED status before dispatch release."
                )
            open_sncrs = self.material_batch.non_conformances.filter(is_resolved=False)
            if open_sncrs.exists():
                blockers.append(
                    f"Material Quality Hold: Batch '{self.material_batch.heat_number}' has {open_sncrs.count()} unresolved Supplier Non-Conformance Report(s) (SNCR)."
                )

        # 2. Production operations & mandatory hold period validation
        ops = ProductionOperation.objects.filter(batch_number=self.batch_or_serial_number)
        if ops.exists():
            incomplete = ops.exclude(status='COMPLETED')
            if incomplete.exists():
                op_names = ", ".join(f"OP-{o.sequence_number} ({o.operation_name})" for o in incomplete)
                blockers.append(f"Incomplete Production Operations: {op_names} must be completed before dispatch.")

            unelapsed = [o for o in ops if not o.is_hold_elapsed]
            if unelapsed:
                hold_details = ", ".join(f"OP-{o.sequence_number} ({o.operation_name}: {o.remaining_hold_seconds // 60}m remaining)" for o in unelapsed)
                blockers.append(f"Mandatory Process Hold Unelapsed: {hold_details} has not satisfied required holding duration.")

        # 3. PDI Inspection record validation
        if not self.inspection_record:
            blockers.append("Inspection Traceability Gap: No Pre-Dispatch Inspection (PDI) record linked to this clearance order.")
        else:
            if self.inspection_record.overall_status != 'PASSED':
                blockers.append(
                    f"Inspection Failure: PDI session #{self.inspection_record.id} status is '{self.inspection_record.get_overall_status_display()}'. All dimensional readings must PASS."
                )
            if self.inspection_record.review_status != 'APPROVED':
                blockers.append(
                    f"Supervisor Sign-Off Missing: PDI session #{self.inspection_record.id} has not been approved by a Shift Supervisor or Quality Manager."
                )

        # 4. State validation
        if self.status == 'CLEARED':
            blockers.append("Dispatch order has already been CLEARED and released for shipment.")

        return blockers

    @property
    def can_be_cleared(self):
        return len(self.get_clearance_blockers()) == 0

    @property
    def is_cleared(self):
        return self.status == 'CLEARED'


