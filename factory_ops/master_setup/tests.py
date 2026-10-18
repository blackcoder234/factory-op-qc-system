from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group

from master_setup.rbac import (
    ROLE_PLANT_MANAGER,
    ROLE_QUALITY_ENGINEER,
    ROLE_QUALITY_MANAGER,
    ROLE_SHIFT_SUPERVISOR,
    ROLE_QA_INSPECTOR,
    ALL_ROLES,
)
from master_setup.models import Department, Machine, Part
from calibration.models import WorkstationLock
from material_intake.models import MaterialBatch

class AuthenticationAndRBACTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Provision all 5 operational groups
        self.groups = {}
        for role in ALL_ROLES:
            self.groups[role], _ = Group.objects.get_or_create(name=role)

        # Create test users with distinct roles
        self.password = "TestSecurityPIN123!"

        self.inspector = User.objects.create_user(
            username="inspector_john", password=self.password, first_name="John", last_name="Inspector"
        )
        self.inspector.groups.add(self.groups[ROLE_QA_INSPECTOR])

        self.supervisor = User.objects.create_user(
            username="supervisor_sarah", password=self.password, first_name="Sarah", last_name="Supervisor"
        )
        self.supervisor.groups.add(self.groups[ROLE_SHIFT_SUPERVISOR])

        self.quality_mgr = User.objects.create_user(
            username="q_manager_alex", password=self.password, first_name="Alex", last_name="Manager"
        )
        self.quality_mgr.groups.add(self.groups[ROLE_QUALITY_MANAGER])

        self.plant_mgr = User.objects.create_user(
            username="plant_mgr_robert", password=self.password, first_name="Robert", last_name="Director"
        )
        self.plant_mgr.groups.add(self.groups[ROLE_PLANT_MANAGER])

        # Test infrastructure
        self.dept = Department.objects.create(name="CNC Bay", code="BAY-01")
        self.machine = Machine.objects.create(name="Haas Mill", machine_code="CNC-M1", department=self.dept)
        self.part = Part.objects.create(part_number="PART-TEST-01", name="Shaft")
        self.batch = MaterialBatch.objects.create(
            purchase_order_number="PO-2026-01",
            heat_number="HEAT-RBAC-01",
            supplier_name="Apex Steel Mill",
            material_grade="AISI 4140",
            lot_size=100,
            part=self.part,
            status="PENDING"
        )

    # 1. Unauthenticated Protection Tests
    def test_unauthenticated_user_redirected_to_login(self):
        """Operational views must reject unauthenticated requests and redirect to /login/."""
        protected_urls = [
            reverse('master_setup:dashboard'),
            reverse('master_setup:department_list'),
            reverse('master_setup:machine_list'),
            reverse('master_setup:part_list'),
            reverse('master_setup:gauge_list'),
            reverse('calibration:machine_lock_list'),
            reverse('calibration:maintenance_log'),
            reverse('material_intake:batch_list'),
            reverse('inspection:checklist_list'),
            reverse('inspection:record_list'),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 302,
                f"URL {url} did not redirect unauthenticated user"
            )
            self.assertIn('/login/', response.url)

    # 2. Authentication Flow Tests
    def test_login_flow_valid_and_invalid_credentials(self):
        """Test valid authentication redirects to dashboard, invalid credentials display error."""
        # Invalid credentials
        res_invalid = self.client.post(reverse('master_setup:login'), {
            'username': 'inspector_john',
            'password': 'WrongPassword!',
        })
        self.assertEqual(res_invalid.status_code, 200)
        self.assertContains(res_invalid, 'Access Denied')

        # Valid credentials
        res_valid = self.client.post(reverse('master_setup:login'), {
            'username': 'inspector_john',
            'password': self.password,
        })
        self.assertRedirects(res_valid, reverse('master_setup:dashboard'))

    # 3. POST Logout Protection Tests
    def test_logout_requires_post(self):
        """GET logout must be rejected with 405 Method Not Allowed."""
        self.client.login(username="inspector_john", password=self.password)
        res_get = self.client.get(reverse('master_setup:logout'))
        self.assertEqual(res_get.status_code, 405)

        # POST logout succeeds
        res_post = self.client.post(reverse('master_setup:logout'))
        self.assertRedirects(res_post, reverse('master_setup:home'))
        # Verify session is cleared
        self.assertNotIn('_auth_user_id', self.client.session)

    # 4. Workstation Lock Permissions
    def test_inspector_cannot_lock_or_unlock_workstation(self):
        """An inspector cannot bypass permissions by manually POSTing to toggle_lock."""
        self.client.login(username="inspector_john", password=self.password)
        url = reverse('calibration:toggle_lock', kwargs={'machine_id': self.machine.id})

        # GET is forbidden
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, 403)

        # POST is forbidden
        res_post = self.client.post(url, {
            'reason_code': 'MANUAL_SUPERVISOR',
            'reason_details': 'Attempted unauthorized lock',
            'supervisor_name': 'Inspector John',
        })
        self.assertEqual(res_post.status_code, 403)

    def test_supervisor_can_lock_and_unlock_workstation(self):
        """A Shift Supervisor is authorized to lock and unlock workstations."""
        self.client.login(username="supervisor_sarah", password=self.password)
        url = reverse('calibration:toggle_lock', kwargs={'machine_id': self.machine.id})

        # Lock machine
        res_lock = self.client.post(url, {
            'reason_code': 'MANUAL_SUPERVISOR',
            'reason_details': 'Safety audit lock',
            'supervisor_name': 'Sarah',
        })
        self.assertRedirects(res_lock, reverse('calibration:machine_lock_list'))
        lock_obj = WorkstationLock.objects.get(machine=self.machine)
        self.assertTrue(lock_obj.is_locked)

        # Unlock machine
        res_unlock = self.client.post(url, {
            'reason_code': 'MANUAL_SUPERVISOR',
            'reason_details': 'Audit completed',
            'supervisor_name': 'Sarah',
        })
        self.assertRedirects(res_unlock, reverse('calibration:machine_lock_list'))
        lock_obj.refresh_from_db()
        self.assertFalse(lock_obj.is_locked)

        # Re-lock and test unlock without reason_code (browser unlock form)
        self.client.post(url, {
            'reason_code': 'MANUAL_SUPERVISOR',
            'reason_details': 'Precautionary lock',
            'supervisor_name': 'Sarah',
        })
        lock_obj.refresh_from_db()
        self.assertTrue(lock_obj.is_locked)

        res_browser_unlock = self.client.post(url, {
            'reason_details': 'Supervisor quality clearance check.',
            'supervisor_name': 'Amarnath Bera (Shift Lead)',
        })
        self.assertRedirects(res_browser_unlock, reverse('calibration:machine_lock_list'))
        lock_obj.refresh_from_db()
        self.assertFalse(lock_obj.is_locked)

    # 5. Material Acceptance Role Enforcement
    def test_inspector_cannot_accept_material_batch(self):
        """A QA Floor Inspector cannot authorize batch acceptance or release to production."""
        self.client.login(username="inspector_john", password=self.password)
        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})

        # Manual POST attempt to accept batch
        res = self.client.post(url, {'action': 'accept_batch'})
        self.assertEqual(res.status_code, 403)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'PENDING')

    def test_quality_manager_can_accept_batch(self):
        """A Quality Manager has authority to approve batch acceptance when all prerequisites are satisfied."""
        from django.core.files.base import ContentFile
        from material_intake.models import ChemicalComposition, MechanicalProperties
        from django.utils import timezone

        # Satisfy prerequisites
        self.batch.mtc_document.save("test_cert.pdf", ContentFile(b"%PDF-1.4 test mtc doc"), save=True)
        ChemicalComposition.objects.create(
            batch=self.batch,
            carbon=0.42,
            manganese=0.80,
            silicon=0.25,
            is_composition_ok=True,
            verified_by="Metallurgist Lab",
            verified_at=timezone.now()
        )
        MechanicalProperties.objects.create(
            batch=self.batch,
            tensile_strength=850.0,
            yield_strength=650.0,
            elongation=16.0,
            hardness=28.0,
            is_properties_ok=True,
            verified_by="QC Engineer",
            verified_at=timezone.now()
        )

        self.client.login(username="q_manager_alex", password=self.password)
        url = reverse('material_intake:batch_detail', kwargs={'batch_id': self.batch.id})

        res = self.client.post(url, {'action': 'accept_batch'})
        self.assertRedirects(res, url)
        self.batch.refresh_from_db()
        self.assertEqual(self.batch.status, 'ACCEPTED')

