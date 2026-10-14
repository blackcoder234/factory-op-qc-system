from django.db import models
from datetime import date

class Department(models.Model):
    """Represents a factory department or shopfloor bay."""
    name = models.CharField(max_length=100, help_text="e.g., Main Machining Shop, Heat Treatment Bay")
    code = models.CharField(max_length=20, unique=True, help_text="Short unique code, e.g. MMS-01")
    location = models.CharField(max_length=200, blank=True, help_text="Physical building / bay location")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department / Factory Site'
        verbose_name_plural = 'Departments / Factory Sites'

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def total_machines(self):
        return self.machines.count()

    @property
    def active_machines(self):
        return self.machines.filter(is_active=True).count()


class Machine(models.Model):
    """A machine tool or workstation on the factory floor."""
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='machines'
    )
    name = models.CharField(max_length=150, help_text="e.g., 5-Axis CNC Milling Center")
    machine_code = models.CharField(max_length=30, unique=True, help_text="e.g., CNC-01, LATHE-04")
    machine_type = models.CharField(max_length=100, blank=True, help_text="e.g. CNC Mill, Lathe, Grinder, CMM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department', 'name']
        verbose_name = 'Machine / Workstation'
        verbose_name_plural = 'Machines / Workstations'

    def __str__(self):
        return f"{self.machine_code} — {self.name}"

    @property
    def is_locked(self):
        """Check if this machine currently has an active workstation lock."""
        if hasattr(self, 'lock_status'):
            return self.lock_status.is_locked
        return False


class Part(models.Model):
    """A manufactured part or component."""
    part_number = models.CharField(max_length=50, unique=True, help_text="e.g., ZP-401-FLANGE")
    name = models.CharField(max_length=150, help_text="e.g., High-Pressure Turbine Flange")
    material_spec = models.CharField(max_length=100, blank=True, help_text="e.g., AISI 4140, SS 316L")
    drawing_number = models.CharField(max_length=50, blank=True, help_text="Engineering blueprint reference")
    revision = models.CharField(max_length=10, default='A', help_text="e.g., Rev A, Rev B")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['part_number']
        verbose_name = 'Manufactured Part / Component'
        verbose_name_plural = 'Manufactured Parts / Components'

    def __str__(self):
        return f"{self.part_number} (Rev {self.revision}) — {self.name}"


class InspectionGauge(models.Model):
    """Measuring gauge/instrument registered with calibration dates."""
    GAUGE_TYPES = [
        ('VERNIER', 'Vernier Caliper'),
        ('MICROMETER', 'External / Internal Micrometer'),
        ('DIAL', 'Dial Bore Gauge'),
        ('HEIGHT', 'Digital Height Gauge'),
        ('CMM', 'CMM Probe / Machine'),
        ('PLUG', 'Thread / Plug Gauge'),
        ('OTHER', 'Other Precision Tool'),
    ]

    serial_number = models.CharField(max_length=50, unique=True, help_text="e.g., VC-104, MIC-022")
    name = models.CharField(max_length=120, help_text="Tool description")
    gauge_type = models.CharField(max_length=20, choices=GAUGE_TYPES, default='VERNIER')
    range_min = models.FloatField(default=0.0, help_text="Minimum range in mm")
    range_max = models.FloatField(default=150.0, help_text="Maximum range in mm")
    resolution = models.FloatField(default=0.01, help_text="Resolution in mm (e.g., 0.01, 0.001)")
    last_calibration_date = models.DateField(null=True, blank=True)
    calibration_due_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, help_text="Tool crib / workstation location")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['serial_number']
        verbose_name = 'Inspection Gauge'
        verbose_name_plural = 'Inspection Gauges'

    def __str__(self):
        return f"{self.serial_number} — {self.name} ({self.get_gauge_type_display()})"

    @property
    def is_calibration_expired(self):
        """Returns True if the calibration due date has passed."""
        if self.calibration_due_date:
            return date.today() > self.calibration_due_date
        return False
