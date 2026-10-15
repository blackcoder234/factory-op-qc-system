from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from master_setup.models import Department, Machine, Part
from master_setup.rbac import (
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
    ROLE_QA_INSPECTOR,
)
from material_intake.models import (
    MaterialBatch,
    ChemicalComposition,
    MechanicalProperties,
    SupplierNonConformance,
)
from material_intake.forms import (
    ChemicalCompositionForm,
    MechanicalPropertiesForm,
    MtcDocumentUploadForm,
)
from material_intake.validators import validate_mtc_document, validate_percentage, validate_positive_finite


class MaterialIntakeEnforcementTests(TestCase):
    """
    Module 3 & Section 9.6: Material Intake, MTC Verification, and Server-Side Gated Acceptance.
    """

    def setUp(self):
        self.password = "SecureQC#2026"

        # Create RBAC Groups
        self.group_qm, _ = Group.objects.get_or_create(name=ROLE_QUALITY_MANAGER)
        self.group_qe, _ = Group.objects.get_or_create(name=ROLE_QUALITY_ENGINEER)
        self.group_supervisor, _ = Group.objects.get_or_create(name=ROLE_SHIFT_SUPERVISOR)
        self.group_inspector, _ = Group.objects.get_or_create(name=ROLE_QA_INSPECTOR)

        # Users
        self.user_qm = User.objects.create_user(username="qm_user", password=self.password)
        self.user_qm.groups.add(self.group_qm)

        self.user_qe = User.objects.create_user(username="qe_user", password=self.password)
        self.user_qe.groups.add(self.group_qe)

        self.user_inspector = User.objects.create_user(username="insp_user", password=self.password)
        self.user_inspector.groups.add(self.group_inspector)

        # Domain objects
        self.dept = Department.objects.create(name="Receiving Bay", code="REC-01")
        self.part = Part.objects.create(part_number="ZP-FLANGE-01", name="Turbine Flange")

        # Create a base batch in PENDING status
        self.batch = MaterialBatch.objects.create(
            purchase_order_number="PO-2026-TEST",
            heat_number="HT-TEST-9001",
            supplier_name="Apex Precision Foundry",
            material_grade="AISI 4140",
            lot_size=120,
            part=self.part,
            status="PENDING",
            received_date=date.today()
        )

    # 1. MTC Document Missing Block
    def test_acceptance_blocked_when_mtc_missing(self):
        """Batch cannot be accepted if original Mill Test Certificate (MTC) is missing."""
        self.client.login(username="qm_user", password=self.password)

        # Setup chemistry & mechanics as OK, but omit MTC file
        ChemicalComposition.objects.create(
            batch=self.batch,
            carbon=0.40, manganese=0.80, silicon=0.25,
            is_composition_ok=True, verified_by="Dr. Chemist", verified_at=timezone.now()
        )
        MechanicalProperties.objects.create(
            batch=self.batch,
            tensile_strength=900.0, yield_strength=750.0, elongation=15.0, hardness=32.0,
            is_properties_ok=True, verified_by="Eng. Smith", verified_at=timezone.now()
        )

        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})
        response = self.client.post(url, {'action': 'accept_batch'})

        self.assertRedirects(response, url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'PENDING')
        self.assertFalse(self.batch.can_be_accepted)
        self.assertTrue(any('MTC' in reason for reason in self.batch.get_acceptance_blockers()))

    # 2. Chemistry Unverified / Failing Block
    def test_acceptance_blocked_when_chemistry_not_conforming(self):
        """Batch cannot be accepted if chemical composition is missing or non-conforming."""
        self.client.login(username="qm_user", password=self.password)

        self.batch.mtc_document.save("test_cert.pdf", ContentFile(b"%PDF-1.4 test certificate"), save=True)
        # Create non-conforming chemistry
        ChemicalComposition.objects.create(
            batch=self.batch,
            carbon=0.85,  # Out of spec
            manganese=0.80,
            silicon=0.25,
            is_composition_ok=False,
            verified_by="Dr. Chemist",
            verified_at=timezone.now()
        )
        MechanicalProperties.objects.create(
            batch=self.batch,
            tensile_strength=900.0, yield_strength=750.0, elongation=15.0, hardness=32.0,
            is_properties_ok=True, verified_by="Eng. Smith", verified_at=timezone.now()
        )

        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})
        response = self.client.post(url, {'action': 'accept_batch'})

        self.assertRedirects(response, url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'PENDING')
        self.assertFalse(self.batch.can_be_accepted)
        self.assertTrue(any('Chemical composition' in reason for reason in self.batch.get_acceptance_blockers()))

    # 3. Mechanical Properties Unverified / Failing Block
    def test_acceptance_blocked_when_mechanics_not_conforming(self):
        """Batch cannot be accepted if mechanical properties do not satisfy criteria."""
        self.client.login(username="qm_user", password=self.password)

        self.batch.mtc_document.save("test_cert.pdf", ContentFile(b"%PDF-1.4 test certificate"), save=True)
        ChemicalComposition.objects.create(
            batch=self.batch,
            carbon=0.40, manganese=0.80, silicon=0.25,
            is_composition_ok=True, verified_by="Dr. Chemist", verified_at=timezone.now()
        )
        MechanicalProperties.objects.create(
            batch=self.batch,
            tensile_strength=500.0,  # Below spec
            yield_strength=300.0,
            elongation=5.0,
            hardness=15.0,
            is_properties_ok=False,
            verified_by="Eng. Smith",
            verified_at=timezone.now()
        )

        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})
        response = self.client.post(url, {'action': 'accept_batch'})

        self.assertRedirects(response, url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'PENDING')
        self.assertFalse(self.batch.can_be_accepted)
        self.assertTrue(any('Mechanical properties' in reason for reason in self.batch.get_acceptance_blockers()))

    # 4. Open SNCR Block
    def test_acceptance_blocked_when_unresolved_sncr_exists(self):
        """Batch cannot be accepted while open Supplier Non-Conformance Reports remain unresolved."""
        self.client.login(username="qm_user", password=self.password)

        self.batch.mtc_document.save("test_cert.pdf", ContentFile(b"%PDF-1.4 test certificate"), save=True)
        ChemicalComposition.objects.create(
            batch=self.batch,
            carbon=0.40, manganese=0.80, silicon=0.25,
            is_composition_ok=True, verified_by="Dr. Chemist", verified_at=timezone.now()
        )
        MechanicalProperties.objects.create(
            batch=self.batch,
            tensile_strength=900.0, yield_strength=750.0, elongation=15.0, hardness=32.0,
            is_properties_ok=True, verified_by="Eng. Smith", verified_at=timezone.now()
        )

        # Create open SNCR
        SupplierNonConformance.objects.create(
            batch=self.batch,
            report_number="SNCR-2026-9999",
            severity="MAJOR",
            defect_category="Packaging Water Ingress",
            disposition_action="Hold in Quarantine",
            reason="Water ingress and surface rust detected on billets",
            raised_by="Quality Inspector",
            is_resolved=False
        )

        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})
        response = self.client.post(url, {'action': 'accept_batch'})

        self.assertRedirects(response, url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'PENDING')
        self.assertFalse(self.batch.can_be_accepted)
        self.assertTrue(any('SNCR' in reason for reason in self.batch.get_acceptance_blockers()))

    # 5. Full Success When All Prerequisites Met
    def test_acceptance_succeeds_when_all_prerequisites_met(self):
        """Quality Manager can successfully accept batch when all verification criteria pass."""
        self.client.login(username="qm_user", password=self.password)

        self.batch.mtc_document.save("test_cert.pdf", ContentFile(b"%PDF-1.4 valid certificate content"), save=True)
        ChemicalComposition.objects.create(
            batch=self.batch,
            carbon=0.41, manganese=0.82, silicon=0.28,
            is_composition_ok=True, verified_by="Dr. K. Mehta", verified_at=timezone.now()
        )
        MechanicalProperties.objects.create(
            batch=self.batch,
            tensile_strength=980.0, yield_strength=820.0, elongation=15.5, hardness=32.0,
            is_properties_ok=True, verified_by="A. Bera", verified_at=timezone.now()
        )

        self.assertTrue(self.batch.can_be_accepted)
        self.assertEqual(len(self.batch.get_acceptance_blockers()), 0)

        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})
        response = self.client.post(url, {'action': 'accept_batch'})

        self.assertRedirects(response, url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'ACCEPTED')

    # 6. Role Authorization
    def test_unauthorized_roles_cannot_accept_batch(self):
        """QA Floor Inspector and Quality Engineer cannot execute acceptance."""
        # Quality Engineer attempt
        self.client.login(username="qe_user", password=self.password)
        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})
        res_qe = self.client.post(url, {'action': 'accept_batch'})
        self.assertEqual(res_qe.status_code, 403)

        # QA Inspector attempt
        self.client.login(username="insp_user", password=self.password)
        res_insp = self.client.post(url, {'action': 'accept_batch'})
        self.assertEqual(res_insp.status_code, 403)

    # 7. MTC Document File Validators
    def test_mtc_document_validator_rejects_disallowed_extensions(self):
        """Executable or unauthorized script files must be rejected by validator."""
        fake_bad_file = SimpleUploadedFile("malicious.exe", b"binary_executable_data", content_type="application/octet-stream")
        with self.assertRaises(ValidationError) as ctx:
            validate_mtc_document(fake_bad_file)
        self.assertIn("Invalid file extension", str(ctx.exception))

    def test_mtc_document_validator_accepts_valid_documents(self):
        """PDF, PNG, JPG, JPEG files must pass file validation."""
        valid_pdf = SimpleUploadedFile("cert.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        valid_png = SimpleUploadedFile("cert.png", b"png_data", content_type="image/png")
        # Should execute without raising
        validate_mtc_document(valid_pdf)
        validate_mtc_document(valid_png)

    # 8. Numeric Validators & Form Cleaning
    def test_chemical_composition_form_requires_verifier_when_marked_ok(self):
        """Form must reject marking composition as conforming without specifying verifying metallurgist."""
        chem = ChemicalComposition.objects.create(batch=self.batch, carbon=0.4, manganese=0.8, silicon=0.2)
        form = ChemicalCompositionForm(data={
            'carbon': 0.40,
            'manganese': 0.80,
            'silicon': 0.25,
            'phosphorus': 0.02,
            'sulfur': 0.02,
            'chromium': 0.95,
            'nickel': 0.10,
            'is_composition_ok': True,
            'verified_by': '',  # Missing verifier
        }, instance=chem)
        self.assertFalse(form.is_valid())
        self.assertIn('verified_by', form.errors)

    def test_numeric_range_validators(self):
        """Percentages must be between 0 and 100, and mechanical properties non-negative."""
        with self.assertRaises(ValidationError):
            validate_percentage(-1.5)
        with self.assertRaises(ValidationError):
            validate_percentage(105.0)
        with self.assertRaises(ValidationError):
            validate_positive_finite(-50.0)

        # Valid calls should not raise
        validate_percentage(0.42)
        validate_positive_finite(950.0)
