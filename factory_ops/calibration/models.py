from django.db import models
from django.utils import timezone
from datetime import date
from master_setup.models import Machine, InspectionGauge

class MaintenanceRecord(models.Model):
    """Preventive Maintenance (PM) and daily setup verification logs."""
    MAINTENANCE_TYPES = [
        ('DAILY_SETUP', 'Daily / Shift Setup Verification'),
        ('PREVENTIVE', 'Periodic Preventive Maintenance (PM)'),
        ('SAFETY', 'Safety Interlock & Emergency Stop Check'),
        ('BREAKDOWN', 'Corrective / Breakdown Repair'),
    ]

    STATUS_CHOICES = [
        ('PASS', 'Verified / Passed'),
        ('FAIL', 'Failed — Maintenance Required'),
        ('PENDING', 'Pending Maintenance'),
    ]

    machine = models.ForeignKey(
        Machine, on_delete=models.CASCADE, related_name='maintenance_records'
    )
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, default='DAILY_SETUP')
    performed_by = models.CharField(max_length=100, help_text="Technician or operator name")
    performed_date = models.DateField(default=timezone.now)
    next_due_date = models.DateField(help_text="Date when next maintenance is required")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PASS')
    checklist_notes = models.TextField(blank=True, help_text="Specific checks (lubrication, coolant, spindle alignment)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_date']
        verbose_name = 'Maintenance Record'
        verbose_name_plural = 'Maintenance Records'

    def __str__(self):
        return f"{self.machine.machine_code} — {self.get_maintenance_type_display()} ({self.performed_date})"

    @property
    def is_overdue(self):
        return date.today() > self.next_due_date


class MachineCalibrationRecord(models.Model):
    """Machine tool calibration history."""
    machine = models.ForeignKey(
        Machine, on_delete=models.CASCADE, related_name='calibration_records'
    )
    calibrated_by = models.CharField(max_length=100, help_text="External calibration agency or internal Metrology lead")
    calibration_date = models.DateField(default=timezone.now)
    next_due_date = models.DateField()
    certificate_number = models.CharField(max_length=50, blank=True, help_text="Calibration certificate / NABL reference")
    result = models.CharField(max_length=10, choices=[('PASS', 'Pass / Within Tolerance'), ('FAIL', 'Fail / Recalibration Needed')], default='PASS')
    deviation_findings = models.TextField(blank=True, help_text="Any measured deviations or offsets applied")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calibration_date']
        verbose_name = 'Machine Calibration Record'
        verbose_name_plural = 'Machine Calibration Records'

    def __str__(self):
        return f"{self.machine.machine_code} Calibration on {self.calibration_date}"


class WorkstationLock(models.Model):
    """
    Workstation safety lock enforcement.
    Blocks job selection and measurement recording if PM or calibration is overdue.
    """
    LOCK_REASONS = [
        ('PM_OVERDUE', 'Preventive Maintenance Overdue'),
        ('CALIBRATION_OVERDUE', 'Machine / Tool Calibration Overdue'),
        ('SAFETY_FAILED', 'Safety Interlock / Emergency Check Failed'),
        ('REPEATED_QC_FAIL', 'Consecutive Quality Non-Conformances'),
        ('MANUAL_SUPERVISOR', 'Manual Supervisor Lock'),
    ]

    machine = models.OneToOneField(
        Machine, on_delete=models.CASCADE, related_name='lock_status'
    )
    is_locked = models.BooleanField(default=False, help_text="True = Workstation is locked; operators cannot begin jobs")
    reason_code = models.CharField(max_length=30, choices=LOCK_REASONS, default='PM_OVERDUE', blank=True)
    reason_details = models.TextField(blank=True, help_text="Supervisor or system explanation for the lock")
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=100, default='System (Auto-Enforcement)', blank=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    unlocked_by = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Workstation Lock'
        verbose_name_plural = 'Workstation Locks'

    def __str__(self):
        status = "LOCKED" if self.is_locked else "OPERATIONAL"
        return f"{self.machine.machine_code} — {status}"

    def trigger_lock(self, reason_code, reason_details, user_name='System'):
        """Helper to lock the workstation and record audit details."""
        self.is_locked = True
        self.reason_code = reason_code
        self.reason_details = reason_details
        self.locked_at = timezone.now()
        self.locked_by = user_name
        self.unlocked_at = None
        self.unlocked_by = ''
        self.save()

    def release_lock(self, user_name='Supervisor'):
        """Helper to unlock the workstation after verification."""
        self.is_locked = False
        self.unlocked_at = timezone.now()
        self.unlocked_by = user_name
        self.save()
