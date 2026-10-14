from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta

from master_setup.models import Department, Machine, Part, InspectionGauge
from calibration.models import MaintenanceRecord, MachineCalibrationRecord, WorkstationLock
from material_intake.models import MaterialBatch, ChemicalComposition, MechanicalProperties, SupplierNonConformance
from inspection.models import InspectionChecklist, ChecklistItem, InspectionRecord, MeasurementReading

class Command(BaseCommand):
    help = 'Seeds realistic manufacturing shopfloor data for FactoryOps QC demo'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Seeding FactoryOps QC demo data..."))

        # 1. DEPARTMENTS
        dept_machining, _ = Department.objects.get_or_create(
            code="MMS-01",
            defaults={
                "name": "Main CNC Machining Shop",
                "location": "Bay 1, Heavy Machining Hall",
                "description": "Houses multi-axis CNC milling, turning centers, and high-speed tapping workstations.",
                "is_active": True,
            }
        )

        dept_heat_treat, _ = Department.objects.get_or_create(
            code="HTB-02",
            defaults={
                "name": "Heat Treatment & Carburizing Bay",
                "location": "Bay 4, Thermal Processing Yard",
                "description": "Controlled-atmosphere furnaces, oil quench tanks, and tempering chambers.",
                "is_active": True,
            }
        )

        dept_metrology, _ = Department.objects.get_or_create(
            code="QCL-03",
            defaults={
                "name": "Quality Assurance & Metrology Lab",
                "location": "Central Inspection Room (Climate Controlled 20°C)",
                "description": "CMM coordinate measuring machines, optical comparators, and surface roughness testers.",
                "is_active": True,
            }
        )

        # 2. MACHINES
        cnc_1, _ = Machine.objects.get_or_create(
            machine_code="CNC-MILL-01",
            defaults={
                "department": dept_machining,
                "name": "Haas VF-4SS 5-Axis Milling Center",
                "machine_type": "CNC Vertical Mill",
                "is_active": True,
            }
        )

        cnc_2, _ = Machine.objects.get_or_create(
            machine_code="CNC-LATHE-02",
            defaults={
                "department": dept_machining,
                "name": "Mazak Quick Turn 250MSY",
                "machine_type": "CNC Turning Center",
                "is_active": True,
            }
        )

        furnace_1, _ = Machine.objects.get_or_create(
            machine_code="FURN-CARB-01",
            defaults={
                "department": dept_heat_treat,
                "name": "Ipsen Sealed Quench Atmosphere Furnace",
                "machine_type": "Heat Treatment Furnace",
                "is_active": True,
            }
        )

        # 3. GAUGES
        gauge_vernier, _ = InspectionGauge.objects.get_or_create(
            serial_number="VC-104",
            defaults={
                "name": "Mitutoyo 500-196-30 Digital Caliper",
                "gauge_type": "VERNIER",
                "range_min": 0.0,
                "range_max": 150.0,
                "resolution": 0.01,
                "last_calibration_date": date.today() - timedelta(days=90),
                "calibration_due_date": date.today() + timedelta(days=275),
                "location": "Workstation CNC-01 Tool Crib",
                "is_active": True,
            }
        )

        gauge_mic, _ = InspectionGauge.objects.get_or_create(
            serial_number="MIC-022",
            defaults={
                "name": "Mitutoyo Outside Micrometer 25-50mm",
                "gauge_type": "MICROMETER",
                "range_min": 25.0,
                "range_max": 50.0,
                "resolution": 0.001,
                "last_calibration_date": date.today() - timedelta(days=400),
                "calibration_due_date": date.today() - timedelta(days=35), # OVERDUE!
                "location": "Metrology Lab Shelf C-3",
                "is_active": True,
            }
        )

        gauge_bore, _ = InspectionGauge.objects.get_or_create(
            serial_number="DBG-015",
            defaults={
                "name": "Fowler Cylinder Bore Dial Indicator",
                "gauge_type": "DIAL",
                "range_min": 50.0,
                "range_max": 160.0,
                "resolution": 0.002,
                "last_calibration_date": date.today() - timedelta(days=60),
                "calibration_due_date": date.today() + timedelta(days=305),
                "location": "Quality Lab Drawer 2",
                "is_active": True,
            }
        )

        # 4. PARTS
        part_flange, _ = Part.objects.get_or_create(
            part_number="ZP-401-FLANGE",
            defaults={
                "name": "High-Pressure Turbine Flange Adaptor",
                "material_spec": "AISI 4140 Quenched & Tempered",
                "drawing_number": "DWG-ZP-2026-04",
                "revision": "B",
                "description": "Critical fluid interface flange with micro-finish sealing face and H7 bore tolerance.",
                "is_active": True,
            }
        )

        part_shaft, _ = Part.objects.get_or_create(
            part_number="ZP-108-SHAFT",
            defaults={
                "name": "Precision Drive Spindle Shaft",
                "material_spec": "SS 316L Stainless Steel",
                "drawing_number": "DWG-ZP-108-S",
                "revision": "A",
                "description": "Ground rotor shaft with keyway and bearing seating collars.",
                "is_active": True,
            }
        )

        # 5. CALIBRATION & WORKSTATION LOCK
        # cnc_1 is healthy
        WorkstationLock.objects.get_or_create(
            machine=cnc_1,
            defaults={
                "is_locked": False,
                "reason_code": "",
                "reason_details": "Machine fully operational. All PM checks and calibrations certified.",
            }
        )

        # cnc_2 is locked due to overdue PM
        lock_cnc2, _ = WorkstationLock.objects.get_or_create(
            machine=cnc_2,
            defaults={
                "is_locked": True,
                "reason_code": "PM_OVERDUE",
                "reason_details": "Spindle vibration check and hydraulic fluid change exceeded 180-day cycle. Job selection disabled.",
                "locked_at": timezone.now() - timedelta(days=2),
                "locked_by": "System Automated Supervisor",
            }
        )

        MaintenanceRecord.objects.get_or_create(
            machine=cnc_1,
            maintenance_type="PREVENTIVE",
            performed_date=date.today() - timedelta(days=15),
            defaults={
                "performed_by": "R. Sharma (Senior Maintenance Tech)",
                "next_due_date": date.today() + timedelta(days=75),
                "status": "PASS",
                "checklist_notes": "Coolant refractometer test: 8.5% Brix. Axis backlash within 0.004mm. Emergency stop switch verified.",
            }
        )

        # 6. RAW MATERIAL INTAKE & MTC
        batch_steel, _ = MaterialBatch.objects.get_or_create(
            heat_number="HT-94821",
            defaults={
                "purchase_order_number": "PO-2026-8812",
                "supplier_name": "Jindal Steel & Alloys Ltd.",
                "part": part_flange,
                "material_grade": "AISI 4140 Alloy Bar",
                "lot_size": 150,
                "unit_of_measure": "Forged Billets",
                "received_date": date.today() - timedelta(days=5),
                "status": "ACCEPTED",
                "dock_inspector": "V. Nair (Dock QA)",
                "notes": "Bundles arrived shrink-wrapped. Color band orange/white matched supplier spec sheet.",
            }
        )

        ChemicalComposition.objects.get_or_create(
            batch=batch_steel,
            defaults={
                "carbon": 0.41,
                "manganese": 0.82,
                "silicon": 0.28,
                "phosphorus": 0.018,
                "sulfur": 0.015,
                "chromium": 0.98,
                "is_composition_ok": True,
                "verified_by": "Dr. K. Mehta (Chief Metallurgist)",
                "verified_at": timezone.now() - timedelta(days=4),
            }
        )

        MechanicalProperties.objects.get_or_create(
            batch=batch_steel,
            defaults={
                "tensile_strength": 980.0,
                "yield_strength": 820.0,
                "elongation": 15.5,
                "hardness": 32.0,
                "hardness_scale": "HRC",
                "is_properties_ok": True,
                "verified_by": "Dr. K. Mehta",
                "verified_at": timezone.now() - timedelta(days=4),
            }
        )

        # Batch 2: Quarantined Batch with SNCR
        batch_quarantine, _ = MaterialBatch.objects.get_or_create(
            heat_number="HT-77209",
            defaults={
                "purchase_order_number": "PO-2026-9044",
                "supplier_name": "Apex Forgings India",
                "part": part_shaft,
                "material_grade": "SS 316L",
                "lot_size": 80,
                "unit_of_measure": "Pieces",
                "received_date": date.today() - timedelta(days=1),
                "status": "REJECTED",
                "dock_inspector": "V. Nair",
                "notes": "Surface pitting and missing sulfur analysis on Mill Test Certificate.",
            }
        )

        SupplierNonConformance.objects.get_or_create(
            batch=batch_quarantine,
            report_number="SNCR-2026-0041",
            defaults={
                "severity": "CRITICAL",
                "defect_category": "Chemistry Deviation & Missing Mill Cert",
                "disposition_action": "Quarantine in Red Bay & Vendor RMA Replacement",
                "reason": "Carbon content measured at 0.082% which exceeds the 0.030% max limit for 316L grade steel. Risk of intergranular corrosion.",
                "raised_by": "A. Bera (QA Lead)",
                "is_resolved": False,
            }
        )

        # 7. INSPECTION CHECKLIST & PDI ITEMS
        checklist_flange, _ = InspectionChecklist.objects.get_or_create(
            name="Turbine Flange Pre-Dispatch Inspection (PDI)",
            part=part_flange,
            defaults={
                "checklist_type": "PDI",
                "revision": "B",
                "operation_step": "OP-50 Final CMM & Bench Inspection",
                "blueprint_reference": "DWG-ZP-2026-04 Sheet 1 Zone D4",
                "is_active": True,
            }
        )

        item_1, _ = ChecklistItem.objects.get_or_create(
            checklist=checklist_flange,
            sequence_number=1,
            defaults={
                "characteristic_name": "Internal Bore Diameter",
                "nominal_value": 50.00,
                "tolerance_plus": 0.02,
                "tolerance_minus": 0.02,
                "measurement_unit": "mm",
                "recommended_gauge": gauge_vernier,
                "is_critical": True,
            }
        )

        item_2, _ = ChecklistItem.objects.get_or_create(
            checklist=checklist_flange,
            sequence_number=2,
            defaults={
                "characteristic_name": "Flange Outer Collar Thickness",
                "nominal_value": 18.50,
                "tolerance_plus": 0.05,
                "tolerance_minus": 0.05,
                "measurement_unit": "mm",
                "recommended_gauge": gauge_vernier,
                "is_critical": False,
            }
        )

        item_3, _ = ChecklistItem.objects.get_or_create(
            checklist=checklist_flange,
            sequence_number=3,
            defaults={
                "characteristic_name": "Bolt Circle PCD Runout",
                "nominal_value": 85.00,
                "tolerance_plus": 0.03,
                "tolerance_minus": 0.03,
                "measurement_unit": "mm",
                "recommended_gauge": gauge_bore,
                "is_critical": True,
            }
        )

        # 8. INSPECTION RECORD WITH AUTO PASS/FAIL
        record_pass, _ = InspectionRecord.objects.get_or_create(
            batch_or_serial_number="BATCH-FLG-001",
            checklist=checklist_flange,
            defaults={
                "machine": cnc_1,
                "inspector_name": "Amarnath Bera (QC Lead)",
                "inspection_date": date.today(),
                "shift": "Shift A (Morning)",
                "remarks": "Part dimensions within specification limits. Approved for dispatch packaging.",
            }
        )

        # Create readings (triggers save() auto Pass/Fail calculation)
        MeasurementReading.objects.get_or_create(
            record=record_pass,
            checklist_item=item_1,
            defaults={"actual_value": 50.012, "used_gauge": gauge_vernier}
        )
        MeasurementReading.objects.get_or_create(
            record=record_pass,
            checklist_item=item_2,
            defaults={"actual_value": 18.520, "used_gauge": gauge_vernier}
        )
        MeasurementReading.objects.get_or_create(
            record=record_pass,
            checklist_item=item_3,
            defaults={"actual_value": 84.995, "used_gauge": gauge_bore}
        )

        self.stdout.write(self.style.SUCCESS("[OK] FactoryOps QC demo data successfully seeded!"))
