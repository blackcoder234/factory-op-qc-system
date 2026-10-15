from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
import math

from master_setup.models import Department, Machine, Part, InspectionGauge
from calibration.models import WorkstationLock
from material_intake.models import MaterialBatch, SupplierNonConformance
from inspection.models import (
    InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading,
    ProductionOperation, DispatchClearance
)
from inspection.forms import InspectionRecordForm, MeasurementReadingForm
from inspection.validators import validate_measurement_value

from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.utils import timezone
from master_setup.rbac import (
    ROLE_QA_INSPECTOR, ROLE_SHIFT_SUPERVISOR, ROLE_QUALITY_MANAGER, ROLE_PLANT_MANAGER
)


class QualityControlEnforcementTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Groups
        grp_inspector, _ = Group.objects.get_or_create(name=ROLE_QA_INSPECTOR)
        grp_supervisor, _ = Group.objects.get_or_create(name=ROLE_SHIFT_SUPERVISOR)
        grp_qm, _ = Group.objects.get_or_create(name=ROLE_QUALITY_MANAGER)

        # Users
        self.user = User.objects.create_user(username="test_qa_inspector", password="password123")
        self.user.groups.add(grp_inspector)

        self.supervisor = User.objects.create_user(username="test_supervisor", password="password123")
        self.supervisor.groups.add(grp_supervisor)

        self.qm = User.objects.create_user(username="test_qm", password="password123")
        self.qm.groups.add(grp_qm)

        self.client.force_login(self.user)

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
        self.gauge_inactive = InspectionGauge.objects.create(
            serial_number="VC-INACTIVE", name="Decommissioned Caliper",
            calibration_due_date=date.today() + timedelta(days=50),
            is_active=False
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

    def test_inactive_gauge_measurement_blocked_in_view(self):
        """System blocks measurement entry if gauge is decommissioned or inactive."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-004", inspector_name="Test Inspector"
        )
        post_data = {
            'action': 'save_reading',
            'item_id': self.item.id,
            'actual_value': '50.010',
            'gauge_id': self.gauge_inactive.id,
        }
        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record.readings.count(), 0)
        self.assertContains(response, 'INACTIVE or decommissioned')

    def test_measurement_reading_finite_numeric_validation(self):
        """NaN, Inf, or invalid values must be rejected by validator and form."""
        with self.assertRaises(ValidationError):
            validate_measurement_value(float('nan'))
        with self.assertRaises(ValidationError):
            validate_measurement_value(float('inf'))
        with self.assertRaises(ValidationError):
            validate_measurement_value("not-a-number")

        # Plausible values succeed
        validate_measurement_value(50.015)
        validate_measurement_value(-0.005)

    def test_incomplete_inspection_cannot_be_approved(self):
        """A session with missing characteristic readings cannot be signed off by a supervisor."""
        self.client.force_login(self.supervisor)

        # Add a 2nd checklist item
        item2 = ChecklistItem.objects.create(
            checklist=self.checklist, sequence_number=2, characteristic_name="Length",
            nominal_value=120.0, tolerance_plus=0.05, tolerance_minus=0.05
        )

        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-INC-01", inspector_name="Operator"
        )
        # Only measure item 1
        MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge_valid
        )

        self.assertFalse(record.can_be_approved)
        self.assertTrue(any('Incomplete' in b for b in record.get_approval_blockers()))

        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, {'action': 'approve_record'}, follow=True)
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.review_status, 'PENDING')
        self.assertContains(response, 'Approval Blocked')

    def test_failing_inspection_cannot_be_approved(self):
        """A session with out-of-tolerance reading cannot be approved by a supervisor."""
        self.client.force_login(self.supervisor)

        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-FAIL-01", inspector_name="Operator"
        )
        MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.050, used_gauge=self.gauge_valid  # Fails
        )

        self.assertFalse(record.can_be_approved)
        self.assertTrue(any('out-of-tolerance' in b for b in record.get_approval_blockers()))

        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, {'action': 'approve_record'}, follow=True)
        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.review_status, 'PENDING')
        self.assertContains(response, 'Approval Blocked')

    def test_supervisor_can_approve_valid_complete_inspection(self):
        """Shift Supervisor can approve a complete, fully conforming inspection session."""
        self.client.force_login(self.supervisor)

        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-VALID-01", inspector_name="Operator"
        )
        MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.012, used_gauge=self.gauge_valid
        )

        self.assertTrue(record.can_be_approved)
        self.assertEqual(len(record.get_approval_blockers()), 0)

        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, {
            'action': 'approve_record',
            'review_notes': 'Dimensions 100% verified against blueprint Rev A.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.review_status, 'APPROVED')
        self.assertEqual(record.reviewed_by, 'test_supervisor')
        self.assertIsNotNone(record.reviewed_at)
        self.assertContains(response, 'successfully reviewed and APPROVED')

    def test_qa_inspector_cannot_approve_inspection(self):
        """QA Floor Inspector is denied authority to approve inspection sessions (403 Forbidden)."""
        self.client.force_login(self.user)  # QA Floor Inspector

        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-PERM-01", inspector_name="Operator"
        )
        MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.012, used_gauge=self.gauge_valid
        )

        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, {'action': 'approve_record'})
        self.assertEqual(response.status_code, 403)

    def test_measurement_reading_rejects_cross_checklist_item(self):
        """Measurement reading must reject checklist item belonging to a different checklist."""
        other_part = Part.objects.create(part_number="PART-999", name="Flange")
        other_checklist = InspectionChecklist.objects.create(name="Flange PDI", part=other_part, checklist_type="PDI")
        other_item = ChecklistItem.objects.create(
            checklist=other_checklist, sequence_number=1, characteristic_name="Flange OD",
            nominal_value=150.0, tolerance_plus=0.1, tolerance_minus=0.1
        )
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-CROSS-01", inspector_name="Test Inspector"
        )
        with self.assertRaises(ValidationError) as ctx:
            MeasurementReading.objects.create(
                record=record, checklist_item=other_item, actual_value=150.0, used_gauge=self.gauge_valid
            )
        self.assertIn("belongs to checklist", str(ctx.exception))

    def test_measurement_reading_rejects_expired_gauge_at_model_level(self):
        """Model-level clean() rejects saving measurement reading with expired gauge."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-EXP-01", inspector_name="Test Inspector"
        )
        with self.assertRaises(ValidationError) as ctx:
            MeasurementReading.objects.create(
                record=record, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge_expired
            )
        self.assertIn("EXPIRED", str(ctx.exception))

    def test_approved_inspection_session_locks_measurement_modifications(self):
        """Once an inspection session is approved by supervisor, measurement readings cannot be added or edited."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-LOCK-01", inspector_name="Operator"
        )
        reading = MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge_valid
        )
        # Supervisor approves
        record.review_status = 'APPROVED'
        record.reviewed_by = 'supervisor_test'
        record.reviewed_at = timezone.now()
        record.save()

        # Attempt to edit reading via ORM
        reading.actual_value = 50.018
        with self.assertRaises(ValidationError) as ctx:
            reading.save()
        self.assertIn("locked against measurement modifications", str(ctx.exception))

        # Attempt to edit reading via HTTP POST
        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, {
            'action': 'save_reading',
            'item_id': self.item.id,
            'actual_value': '50.018',
            'gauge_id': self.gauge_valid.id
        }, follow=True)
        self.assertContains(response, 'locked by supervisor')

    def test_update_overall_status_resets_approved_status_if_reading_fails(self):
        """If an approved record's overall status changes to FAILED, approval status is reset to PENDING."""
        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-RESET-01", inspector_name="Operator"
        )
        reading = MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge_valid
        )
        record.review_status = 'APPROVED'
        record.reviewed_by = 'supervisor_test'
        record.reviewed_at = timezone.now()
        record.save()

        # Force a failing reading in database directly
        MeasurementReading.objects.filter(id=reading.id).update(actual_value=999.0, result='FAIL')
        record.update_overall_status()

        record.refresh_from_db()
        self.assertEqual(record.overall_status, 'FAILED')
        self.assertEqual(record.review_status, 'PENDING')
        self.assertEqual(record.reviewed_by, '')

    def test_supervisor_can_reject_failing_inspection(self):
        """Shift Supervisor can formally reject an out-of-spec inspection session."""
        self.client.force_login(self.supervisor)

        record = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine_op,
            batch_or_serial_number="B-REJ-01", inspector_name="Operator"
        )
        MeasurementReading.objects.create(
            record=record, checklist_item=self.item, actual_value=50.060, used_gauge=self.gauge_valid
        )

        url = reverse('inspection:record_detail', kwargs={'record_id': record.id})
        response = self.client.post(url, {
            'action': 'reject_record',
            'review_notes': 'Non-conforming bore dimension. Quarantined for scrap review.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.review_status, 'REJECTED')
        self.assertEqual(record.overall_status, 'FAILED')
        self.assertEqual(record.reviewed_by, 'test_supervisor')
        self.assertContains(response, 'marked as REJECTED')


class DispatchClearanceQualityGateTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Groups
        grp_inspector, _ = Group.objects.get_or_create(name=ROLE_QA_INSPECTOR)
        grp_supervisor, _ = Group.objects.get_or_create(name=ROLE_SHIFT_SUPERVISOR)
        grp_qm, _ = Group.objects.get_or_create(name=ROLE_QUALITY_MANAGER)
        grp_gm, _ = Group.objects.get_or_create(name=ROLE_PLANT_MANAGER)

        # Users
        self.inspector = User.objects.create_user(username="test_inspector", password="password123")
        self.inspector.groups.add(grp_inspector)

        self.supervisor = User.objects.create_user(username="test_supervisor", password="password123")
        self.supervisor.groups.add(grp_supervisor)

        self.qm = User.objects.create_user(username="test_qm", password="password123")
        self.qm.groups.add(grp_qm)

        self.gm = User.objects.create_user(username="test_gm", password="password123")
        self.gm.groups.add(grp_gm)

        # Base models
        self.dept = Department.objects.create(name="Machining Bay", code="MB-01")
        self.machine = Machine.objects.create(name="CNC Lathe 1", machine_code="CNC-01", department=self.dept)
        self.part = Part.objects.create(part_number="PART-FLANGE", name="Precision Flange")
        self.checklist = InspectionChecklist.objects.create(name="Flange PDI", part=self.part, checklist_type="PDI")
        self.gauge = InspectionGauge.objects.create(
            serial_number="VC-01", name="Digital Caliper", calibration_due_date=date.today() + timedelta(days=100)
        )
        self.item = ChecklistItem.objects.create(
            checklist=self.checklist, sequence_number=1, characteristic_name="Outer Diameter",
            nominal_value=50.00, tolerance_plus=0.02, tolerance_minus=0.02, recommended_gauge=self.gauge
        )

        # Material batch (ACCEPTED)
        self.material_accepted = MaterialBatch.objects.create(
            heat_number="HT-TEST-001", purchase_order_number="PO-101",
            supplier_name="Steel Corp", part=self.part, material_grade="AISI 4140",
            lot_size=100, received_date=date.today(), status="ACCEPTED"
        )

        # Material batch (QUARANTINE)
        self.material_quarantine = MaterialBatch.objects.create(
            heat_number="HT-TEST-002", purchase_order_number="PO-102",
            supplier_name="Alloy Ltd", part=self.part, material_grade="AISI 4140",
            lot_size=50, received_date=date.today(), status="QUARANTINE"
        )

        # PDI Record (PASSED and APPROVED)
        self.pdi_passed = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine,
            batch_or_serial_number="BATCH-DISP-01", inspector_name="Test Inspector",
            overall_status="PASSED", review_status="PENDING",
        )
        MeasurementReading.objects.create(
            record=self.pdi_passed, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge
        )
        self.pdi_passed.review_status = "APPROVED"
        self.pdi_passed.reviewed_by = "test_supervisor"
        self.pdi_passed.reviewed_at = timezone.now()
        self.pdi_passed.save()

        # PDI Record (FAILED)
        self.pdi_failed = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine,
            batch_or_serial_number="BATCH-DISP-02", inspector_name="Test Inspector",
            overall_status="FAILED", review_status="PENDING_REVIEW"
        )
        MeasurementReading.objects.create(
            record=self.pdi_failed, checklist_item=self.item, actual_value=50.080, used_gauge=self.gauge
        )

        # Completed production operations for BATCH-DISP-01
        ProductionOperation.objects.create(
            batch_number="BATCH-DISP-01",
            sequence_number=10,
            part=self.part,
            operation_name="Turning & Facing",
            status="COMPLETED"
        )

    def test_dispatch_blocked_when_production_operations_missing(self):
        """Dispatch is blocked if no manufacturing operations are recorded for the batch."""
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-NO-OPS",
            part=self.part,
            batch_or_serial_number="BATCH-WITHOUT-OPS",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=10,
            destination="Customer Hub"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Routing Traceability Gap" in b for b in blockers))

    def test_dispatch_blocked_without_material_batch(self):
        """Dispatch order without raw material linkage cannot be cleared."""
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-001",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=None,
            inspection_record=self.pdi_passed,
            quantity=10,
            destination="Customer Hub A"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Material Traceability Gap" in b for b in blockers))

    def test_dispatch_blocked_if_material_not_accepted(self):
        """Material in QUARANTINE or REJECTED status blocks dispatch clearance."""
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-002",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=self.material_quarantine,
            inspection_record=self.pdi_passed,
            quantity=10,
            destination="Customer Hub B"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Raw material batch" in b and "ACCEPTED" in b for b in blockers))

    def test_dispatch_blocked_if_unresolved_sncr(self):
        """Material batch with open SupplierNonConformance report blocks clearance."""
        SupplierNonConformance.objects.create(
            batch=self.material_accepted,
            report_number="SNCR-TEST-99",
            severity="MAJOR",
            defect_category="Surface Cracks",
            reason="Surface cracking observed during inspection",
            raised_by="Quality Engineer",
            is_resolved=False
        )
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-003",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=10,
            destination="Customer Hub C"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Material Quality Hold" in b and "SNCR" in b for b in blockers))

    def test_dispatch_blocked_if_production_operations_incomplete(self):
        """Batch with unfinished production operations is blocked from dispatch release."""
        ProductionOperation.objects.create(
            batch_number="BATCH-DISP-OPS",
            sequence_number=10,
            part=self.part,
            operation_name="Turning",
            status="COMPLETED"
        )
        ProductionOperation.objects.create(
            batch_number="BATCH-DISP-OPS",
            sequence_number=20,
            part=self.part,
            operation_name="Boring",
            status="IN_PROGRESS"
        )
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-004",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-OPS",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=10,
            destination="Customer Hub D"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Incomplete Production Operations" in b for b in blockers))

    def test_dispatch_blocked_if_mandatory_hold_period_unelapsed(self):
        """Batch with active/unelapsed mandatory stress-relief hold period is blocked."""
        ProductionOperation.objects.create(
            batch_number="BATCH-DISP-HOLD",
            sequence_number=10,
            part=self.part,
            operation_name="Thermal Soak",
            status="COMPLETED",
            hold_duration_hours=4.0,
            hold_started_at=timezone.now() - timedelta(hours=1)  # Only 1 hour elapsed out of 4
        )
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-005",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-HOLD",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=10,
            destination="Customer Hub E"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Mandatory Process Hold Unelapsed" in b for b in blockers))

    def test_dispatch_blocked_if_pdi_inspection_missing_or_failed(self):
        """Dispatch without PDI or with failed PDI cannot be cleared."""
        # Missing PDI
        dispatch_no_pdi = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-006A",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=self.material_accepted,
            inspection_record=None,
            quantity=10,
            destination="Customer Hub"
        )
        self.assertFalse(dispatch_no_pdi.can_be_cleared)
        self.assertTrue(any("Inspection Traceability Gap" in b for b in dispatch_no_pdi.get_clearance_blockers()))

        # Failed PDI
        dispatch_failed_pdi = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-006B",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-02",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_failed,
            quantity=10,
            destination="Customer Hub"
        )
        self.assertFalse(dispatch_failed_pdi.can_be_cleared)
        self.assertTrue(any("Inspection Failure" in b for b in dispatch_failed_pdi.get_clearance_blockers()))

    def test_dispatch_blocked_if_pdi_not_approved(self):
        """PDI session that passed dimensions but lacks supervisor approval blocks clearance."""
        pdi_unapproved = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine,
            batch_or_serial_number="BATCH-DISP-03", inspector_name="Test Inspector",
            overall_status="PASSED", review_status="PENDING_REVIEW"
        )
        MeasurementReading.objects.create(
            record=pdi_unapproved, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge
        )
        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-007",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-03",
            material_batch=self.material_accepted,
            inspection_record=pdi_unapproved,
            quantity=10,
            destination="Customer Hub"
        )
        blockers = dispatch.get_clearance_blockers()
        self.assertFalse(dispatch.can_be_cleared)
        self.assertTrue(any("Supervisor Sign-Off Missing" in b for b in blockers))

    def test_dispatch_authorized_success_by_quality_manager(self):
        """Quality Manager can authorize dispatch release when all 4 gates pass."""
        self.client.force_login(self.qm)

        # Complete operation with elapsed hold
        ProductionOperation.objects.create(
            batch_number="BATCH-DISP-OK",
            sequence_number=10,
            part=self.part,
            operation_name="Machining & Quench",
            status="COMPLETED",
            hold_duration_hours=1.0,
            hold_started_at=timezone.now() - timedelta(hours=2)
        )

        pdi_ok = InspectionRecord.objects.create(
            checklist=self.checklist, machine=self.machine,
            batch_or_serial_number="BATCH-DISP-OK", inspector_name="Test Inspector",
            overall_status="PASSED", review_status="PENDING",
        )
        MeasurementReading.objects.create(
            record=pdi_ok, checklist_item=self.item, actual_value=50.010, used_gauge=self.gauge
        )
        pdi_ok.review_status = "APPROVED"
        pdi_ok.reviewed_by = "test_supervisor"
        pdi_ok.reviewed_at = timezone.now()
        pdi_ok.save()

        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-008",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-OK",
            material_batch=self.material_accepted,
            inspection_record=pdi_ok,
            quantity=20,
            destination="Airbus Hamburg Plant"
        )

        self.assertTrue(dispatch.can_be_cleared)
        self.assertEqual(len(dispatch.get_clearance_blockers()), 0)

        url = reverse('inspection:dispatch_detail', kwargs={'dispatch_id': dispatch.id})
        response = self.client.post(url, {
            'action': 'clear_dispatch',
            'clearance_notes': 'Full zero-escape audit cleared. Released for shipping.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        dispatch.refresh_from_db()
        self.assertEqual(dispatch.status, 'CLEARED')
        self.assertEqual(dispatch.cleared_by, self.qm)
        self.assertIsNotNone(dispatch.cleared_at)
        self.assertContains(response, 'DISPATCH RELEASE AUTHORIZED')

    def test_dispatch_authorized_success_by_plant_manager(self):
        """Plant / General Manager can also authorize dispatch release."""
        self.client.force_login(self.gm)

        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-009",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=15,
            destination="Alstom Rail Bay 2"
        )
        self.assertTrue(dispatch.can_be_cleared)

        url = reverse('inspection:dispatch_detail', kwargs={'dispatch_id': dispatch.id})
        response = self.client.post(url, {'action': 'clear_dispatch'}, follow=True)

        self.assertEqual(response.status_code, 200)
        dispatch.refresh_from_db()
        self.assertEqual(dispatch.status, 'CLEARED')
        self.assertEqual(dispatch.cleared_by, self.gm)

    def test_dispatch_authorization_forbidden_for_qa_inspector(self):
        """QA Floor Inspector is denied authority to clear dispatch (403 Forbidden)."""
        self.client.force_login(self.inspector)

        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-010",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=15,
            destination="Alstom Rail"
        )
        url = reverse('inspection:dispatch_detail', kwargs={'dispatch_id': dispatch.id})
        response = self.client.post(url, {'action': 'clear_dispatch'})
        self.assertEqual(response.status_code, 403)

    def test_dispatch_rejection_by_quality_manager(self):
        """Quality Manager can place a dispatch order on quality hold / quarantine."""
        self.client.force_login(self.qm)

        dispatch = DispatchClearance.objects.create(
            dispatch_order_number="DSP-TEST-011",
            part=self.part,
            batch_or_serial_number="BATCH-DISP-01",
            material_batch=self.material_accepted,
            inspection_record=self.pdi_passed,
            quantity=15,
            destination="Customer Plant"
        )
        url = reverse('inspection:dispatch_detail', kwargs={'dispatch_id': dispatch.id})
        response = self.client.post(url, {
            'action': 'reject_dispatch',
            'clearance_notes': 'Packaging damage detected on dock. Holding for repackaging.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        dispatch.refresh_from_db()
        self.assertEqual(dispatch.status, 'REJECTED')
        self.assertEqual(dispatch.cleared_by, self.qm)
        self.assertContains(response, 'DISPATCH ORDER REJECTED')
