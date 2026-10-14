from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta

from master_setup.models import Department, Machine, Part, InspectionGauge
from calibration.models import WorkstationLock
from inspection.models import InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading
from inspection.forms import InspectionRecordForm

class QualityControlEnforcementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Machining Bay", code="MB-01")
        self.machine_op = Machine.objects.create(name="CNC Lathe 1", machine_code="CNC-01", department=self.dept)
        self.machine_locked = Machine.objects.create(name="CNC Mill 2", machine_code="CNC-02", department=self.dept)
        WorkstationLock.objects.create(machine=self.machine_locked, is_locked=True, reason_code="PM_OVERDUE")

        self.part = Part.objects.create(part_number="PART-100", name="Gear Shaft")
        self.checklist = InspectionChecklist.objects.create(name="Shaft PDI", part=self.part, checklist_type="PDI")
        
        self.gauge_valid = InspectionGauge.objects.create(
            serial_number="VC-01", name="Digital Caliper",
            calibration_due_date=date.today() + timedelta(days=100)
        )
        self.gauge_expired = InspectionGauge.objects.create(
            serial_number="VC-EXPIRED", name="Old Caliper",
            calibration_due_date=date.today() - timedelta(days=10)
        )

        self.item = ChecklistItem.objects.create(
            checklist=self.checklist,
            sequence_number=1,
            characteristic_name="Outer Diameter",
            nominal_value=50.00,
            tolerance_plus=0.02,
            tolerance_minus=0.02,
            recommended_gauge=self.gauge_valid
        )

    def test_tolerance_auto_evaluation_pass(self):
        """Test that a measurement within nominal +/- tolerance automatically evaluates to PASS."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-001", inspector_name="Test Inspector"
        )
        reading = MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.015, used_gauge=self.gauge_valid
        )
        self.assertEqual(reading.result, 'PASS')
        record.refresh_from_db()
        self.assertEqual(record.overall_status, 'PASSED')

    def test_tolerance_auto_evaluation_fail(self):
        """Test that a measurement out of tolerance automatically evaluates to FAIL."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-002", inspector_name="Test Inspector"
        )
        reading = MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.035, used_gauge=self.gauge_valid
        )
        self.assertEqual(reading.result, 'FAIL')
        record.refresh_from_db()
        self.assertEqual(record.overall_status, 'FAILED')

    def test_workstation_lock_prohibits_inspection_creation(self):
        """Test BRD Module 2: System rejects launching an inspection on a locked workstation."""
        form_data = {
            'checklist': self.checklist.id,
            'machine': self.machine_locked.id,
            'batch_or_serial_number': 'B-LOCK-01',
            'inspector_name': 'Tester',
            'inspection_date': date.today(),
            'shift': 'Shift A (Morning)',
            'remarks': 'Test',
        }
        form = InspectionRecordForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('machine', form.errors)
        self.assertIn('LOCKED', form.errors['machine'][0])

    def test_expired_gauge_measurement_blocked_in_view(self):
        """Test BRD Module 2: System blocks measurement entry if gauge calibration is expired."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-003", inspector_name="Test Inspector"
        )
        post_data = {
            'action': 'save_reading',
            'item_id': self.item.id,
            'actual_value': '50.010',
            'gauge_id': self.gauge_expired.id,
        }
        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Verify no reading was saved
        self.assertEqual(record.readings.count(), 0)
        self.assertContains(response, 'MEASUREMENT ENTRY BLOCKED')
