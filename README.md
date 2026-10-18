<div align="center">

# 🏭 Factory Operations & Quality Control System (FactoryOps QC)

### Enterprise Shopfloor Quality Assurance & Zero-Escape Interlock Safety Platform

Built for **Zapuza Technologies LLP** — Python Django Developer Internship Assessment  
Facility: **Apex Precision Dynamics Ltd. — Plant APX-09**

[![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-49%20Passed%20%E2%9C%93-emerald?style=for-the-badge)](#-automated-testing-suite)
[![Security](https://img.shields.io/badge/Security-RBAC%20%26%20Zero--Escape-blue?style=for-the-badge)](#-security--production-hardening)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Video Demo](https://img.shields.io/badge/Video_Demo-Watch_Walkthrough-4285F4?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1gjS2rAMI9YCtLBuhqdNpO-WHZc0bs_dZ/view?usp=sharing)

</div>

---

## 📌 Executive Summary

In precision mechanical manufacturing facilities, paper logbooks and manual inspection checklists lead to quality escapes, overdue machine tool operations, and untraceable metallurgical deviations.

**FactoryOps QC** digitizes the shopfloor manufacturing quality lifecycle into a unified, audit-compliant web application. Built for **Apex Precision Dynamics (Plant APX-09)**, the platform replaces manual tracking with server-side enforced digital quality gates, strict role-based access control (RBAC), instrument calibration tracking, and an atomic zero-escape dispatch clearance workflow architected around ISO 9001 quality management principles.

---

## 🎥 Video Demonstration & Code Walkthrough

> 📺 **Video Walkthrough:** **[▶ Watch the FactoryOps QC System Walkthrough & Code Explanation](https://drive.google.com/file/d/1gjS2rAMI9YCtLBuhqdNpO-WHZc0bs_dZ/view?usp=sharing)**

---

## 🏗️ 5 Core Operational Modules & Quality Pillars

<table>
  <thead>
    <tr>
      <th width="28%">Operational Module</th>
      <th>Quality Assurance Scope & Server-Side Interlocks</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>🏭 <b>Module 1: Master Setup</b></td>
      <td>
        Registers factory manufacturing departments, CNC workstation telemetry, engineered parts (with blueprint drawing numbers and CAD revisions), and precision gauges with calibration due date tracking.
      </td>
    </tr>
    <tr>
      <td>🔒 <b>Module 2: Calibration &amp; Workstation Lock</b></td>
      <td>
        Enforces preventive maintenance (PM) schedules. Automatically detects overdue equipment and disables job selection and measurement recording via safety interlocks to prevent out-of-spec production.
      </td>
    </tr>
    <tr>
      <td>📦 <b>Module 3: Material Intake &amp; MTC Verification</b></td>
      <td>
        Inward dock receiving workflow tracking supplier heat numbers, purchase orders, chemical composition tolerances (C, Mn, Si, P, S), mechanical properties (UTS, YS, Hardness, Elongation), and Supplier Non-Conformance (SNCR) quarantine flows. Features strict document validation (10MB limit, binary magic byte signature verification for PDF, PNG, JPG, TIFF, zero-byte file rejection, sanitized filenames) and multi-point server-side batch acceptance gating with audit trail recording (<code>accepted_by</code>, <code>accepted_at</code>).
      </td>
    </tr>
    <tr>
      <td>📐 <b>Module 4: Quality Inspections &amp; PDI</b></td>
      <td>
        Inspection checklist template studio defining nominal dimensions and tolerances ($50.00 \pm 0.02\text{ mm}$) with real-time automated <b>PASS / FAIL</b> evaluation upon measurement entry. Enforces finite numeric float validation, rejects expired/inactive measuring instruments, validates checklist-item ownership, locks approved sessions against post-approval tampering, and requires formal supervisor sign-off before downstream processing.
      </td>
    </tr>
    <tr>
      <td>🚢 <b>Module 5: Zero-Escape Dispatch Clearance</b></td>
      <td>
        Database-backed shipping release gate linking finished parts to raw material heat lots, intermediate shopfloor routing operations, mandatory process hold periods (e.g. stress relief cooling), and approved PDI inspection records. Requires that manufacturing routing operations exist and are completed; an empty routing strictly blocks clearance. Release authorization requires Quality Manager or Plant Manager sign-off wrapped in atomic database locks.
      </td>
    </tr>
  </tbody>
</table>

---

## 🔐 Standardized Role-Based Access Control (RBAC)

The application implements a 5-role operational hierarchy enforced at the server level via Django Groups and custom view decorators (`@role_required` and `check_action_permission`). Unauthorized actions are rejected with HTTP 403 Forbidden pages:

| Operational Role            | Typical Persona             | Permissions & Operational Scope                                                                                                                         |
| --------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Plant / General Manager** | Plant Director              | Full plant oversight, workstation lock management, and final shipping dispatch clearance release authority.                                             |
| **Quality Engineer**        | Metrology Engineer          | Setup management, MTC document & metallurgical verification, checklist template creation, and dimensional measurement entry.                            |
| **Quality Manager**         | Head of Quality Assurance   | Unrestricted quality authority: material batch release acceptance, checklist authoring, inspection sign-off, and final dispatch clearance.              |
| **Shift Supervisor**        | Shopfloor Lead              | Workstation lockout/release, maintenance logging, inspection session creation, and supervisor sign-off approval.                                        |
| **QA Floor Inspector**      | Receiving & Floor Inspector | Inward material dock logging, starting inspection sessions, and recording physical dimensional readings. Blocked from approving or clearing dispatches. |

### Server-Side Permission Matrix

| Action / Endpoint                  | Floor Inspector | Shift Supervisor | Quality Engineer | Quality Manager | Plant Manager |
| ---------------------------------- | :-------------: | :--------------: | :--------------: | :-------------: | :-----------: |
| **Dock Material Intake**           |       ✅        |        ✅        |        ✅        |       ✅        |      ✅       |
| **Verify MTC Chemistry/Mechanics** |       ❌        |        ❌        |        ✅        |       ✅        |      ❌       |
| **Accept Material Batch Gate**     |       ❌        |        ❌        |        ❌        |       ✅        |      ❌       |
| **Lock / Unlock Workstations**     |       ❌        |        ✅        |        ❌        |       ✅        |      ✅       |
| **Create Checklist Templates**     |       ❌        |        ❌        |        ✅        |       ✅        |      ❌       |
| **Enter Dimensional Measurements** |       ✅        |        ❌        |        ✅        |       ✅        |      ❌       |
| **Approve / Sign Off Inspection**  |       ❌        |        ✅        |        ❌        |       ✅        |      ❌       |
| **Authorize Dispatch Clearance**   |       ❌        |        ❌        |        ❌        |       ✅        |      ✅       |

---

## 🛡️ Security & Production Hardening

- **Dynamic Environment Loading**: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and admin credentials are loaded from environment variables (`.env`) via `python-dotenv`.
- **Fail-Closed Production Default**: `DEBUG` defaults to `False` if not set; `SECRET_KEY` raises an immediate `ImproperlyConfigured` exception in production if missing.
- **CSRF-Protected State Changes**: All state mutations (locking workstations, saving readings, approving records, and logging out) use CSRF-protected `POST` requests. `GET /logout/` is rejected with `405 Method Not Allowed`.
- **Zero Exposed Demo Credentials**: Public login page autofill credentials and displayed passwords have been removed and replaced with a plant security terminal notice.
- **Binary Magic-Byte Upload Validation**: Uploaded Mill Test Certificates are validated against a 10MB limit and inspected for magic byte file signatures (`%PDF-`, `\x89PNG\r\n\x1a\n`, `\xff\xd8\xff`, `II*\x00`/`MM\x00*`) and zero-byte rejection, preventing disguised or spoofed binary uploads.
- **Finiteness & Overflow Protection**: All measurement inputs are validated against non-finite values (`NaN`, `Infinity`) and clamped within physically realistic bounds.
- **Approval Immutability & Status Integrity**: Approved inspection records are locked against measurement modifications. Any status re-evaluation that results in a failure automatically resets supervisor approval to `PENDING`.
- **Concurrency & Routing Protection**: Dispatch clearance authorization is protected with `transaction.atomic()` and `select_for_update()` to prevent race conditions during shipping release. Dispatch is unconditionally blocked if production routing operations are missing or incomplete.
- **Standards Alignment Notice**: Designed and hardened as an internship assessment demonstration platform architected around ISO 9001 quality management principles, without claiming formal accredited laboratory certification.

---

## 📁 Architecture & Decoupled Apps

```text
factory-op-qc-system/
│
├── factory_ops/                     # Django Project Root
│   ├── manage.py                    # Django CLI Management Tool
│   ├── package.json                 # Tailwind CSS v4 build script
│   │
│   ├── factory_ops/                 # Core Configuration
│   │   ├── settings.py              # Environment config, security middleware, DB settings
│   │   ├── urls.py                  # Master URL routing table
│   │   └── wsgi.py                  # WSGI application entrypoint
│   │
│   ├── master_setup/                # Module 1: Master Factory Infrastructure
│   │   ├── models.py                # Department, Machine, Part, InspectionGauge
│   │   ├── rbac.py                  # 5 Standardized Roles, decorators, permission checks
│   │   ├── context_processors.py    # Primary role injection for navbar profile badge
│   │   └── management/commands/     # 'seed_data' realistic demonstration data generator
│   │
│   ├── calibration/                 # Module 2: Workstation Locks & PM Schedules
│   │   ├── models.py                # WorkstationLock, MaintenanceRecord, MachineCalibrationRecord
│   │   └── views.py                 # Lockout toggles with role-based checks
│   │
│   ├── material_intake/             # Module 3: Raw Materials & MTC Conformance
│   │   ├── models.py                # MaterialBatch, ChemicalComposition, MechanicalProperties, SNCR
│   │   ├── validators.py            # MTC upload validation, percentage bounds, finite numbers
│   │   └── views.py                 # Dock receiving, MTC upload, acceptance gate
│   │
│   ├── inspection/                  # Modules 4 & 5: Dimensional QC & Dispatch Clearance
│   │   ├── models.py                # InspectionRecord, ChecklistItem, MeasurementReading,
│   │   │                            # ProductionOperation, DispatchClearance
│   │   ├── validators.py            # validate_measurement_value (NaN/Inf protection)
│   │   ├── forms.py                 # Tolerance entry, gauge calibration checks, dispatch forms
│   │   └── views.py                 # Live inspection entry, supervisor review, dispatch release
│   │
│   ├── templates/                   # Clean, dark-mode industrial DTL templates
│   │   ├── base.html                # Navigation, flash messages, user role badge, POST logout
│   │   ├── 403.html                 # Custom industrial HTTP 403 Access Denied page
│   │   ├── landing.html             # Public plant overview and statistics
│   │   ├── auth/login.html          # Secure terminal authentication
│   │   ├── master_setup/            # Department, machine, gauge, dashboard views
│   │   ├── material_intake/         # Receiving lists, MTC audit cards, acceptance gates
│   │   └── inspection/              # Checklists, PDI sheets, dispatch release gates
│   │
│   ├── static/css/                  # Compiled Tailwind CSS v4 assets
│   └── media/                       # Uploaded Mill Test Certificates
│
├── requirements.txt                 # Pinned Python package dependencies
├── .env.example                     # Environment configuration template
└── README.md                        # Documentation & setup guide
```

---

## 🛠️ Technology Stack

| Layer                 | Technology                             | Details & Rationale                                                              |
| --------------------- | -------------------------------------- | -------------------------------------------------------------------------------- |
| **Backend Framework** | **Python 3.10+ / Django 5.2**          | Battery-packed ORM, secure authentication, CSRF protection, and migration engine |
| **Styling & Design**  | **Tailwind CSS v4 + Vanilla CSS**      | Custom dark industrial design system with emerald/rose status semantics          |
| **Typography**        | **Plus Jakarta Sans & JetBrains Mono** | High-contrast monospace fonts for tolerances, heat numbers, and readings         |
| **Database**          | **SQLite (Dev) / PostgreSQL Ready**    | Multi-table relational integrity with atomic transactions and row-level locking  |
| **File Storage**      | **Django FileField**                   | Validated, hashed storage for supplier Mill Test Certificates (PDF/images)       |
| **Environment**       | **python-dotenv**                      | Explicit environment variable separation for zero credentials in git             |

---

## 🚀 Local Setup & Installation

### 1. Prerequisites

- **Python 3.10** or higher
- **Git**
- **Node.js 18+** _(optional, only if recompiling Tailwind CSS)_

### 2. Clone the Repository

```bash
git clone https://github.com/blackcoder234/factory-op-qc-system.git
cd factory-op-qc-system
```

### 3. Create & Activate Virtual Environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the template configuration file:

```bash
cp factory_ops/.env.example factory_ops/.env
```

Edit `factory_ops/.env`:

```env
SECRET_KEY=generate-a-secure-random-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SEED_ADMIN_PASSWORD=YourSecurePassword123!
```

### 6. Apply Database Migrations

```bash
cd factory_ops
python manage.py migrate
```

### 7. Populate Realistic Factory Demo Data

Populates plant departments, CNC machines, precision gauges, steel heats, PDI inspection sessions, production operations, and dispatch clearance records:

```bash
python manage.py seed_data --admin-password ApexQC#2026
```

_Note: This command provisions the 5 standard operational roles, sets up realistic simulated shopfloor records, and configures the standard evaluation test accounts (`supervisor`, `amarnath`, `inspector`, `engineer`, `plant_manager` with default password `ApexQC#2026` as detailed in `.env.example`)._

### 8. Run the Development Server

```bash
python manage.py runserver
```

Open your browser:

- **Plant Overview Dashboard:** [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Workstation Lock Board:** [http://127.0.0.1:8000/calibration/](http://127.0.0.1:8000/calibration/)
- **Raw Material Intake & MTC:** [http://127.0.0.1:8000/materials/](http://127.0.0.1:8000/materials/)
- **Quality Inspections (PDI):** [http://127.0.0.1:8000/inspection/records/](http://127.0.0.1:8000/inspection/records/)
- **Dispatch Clearance Gate:** [http://127.0.0.1:8000/inspection/dispatch/](http://127.0.0.1:8000/inspection/dispatch/)
- **Django Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Automated Testing Suite

The repository includes **49 automated unit and integration tests** testing all core business rules and security controls:

```bash
cd factory_ops
python manage.py test
```

### Test Suite Execution Output

```text
Creating test database for alias 'default'...
Found 49 test(s).
System check identified no issues (0 silenced).
.................................................
----------------------------------------------------------------------
Ran 49 tests in 119.200s

OK
Destroying test database for alias 'default'...
```

### Test Coverage Highlights

- **Authentication & RBAC (`master_setup/tests.py`)**: Tests login redirects, CSRF-protected POST logout, group role assignments, and 403 Forbidden enforcement on restricted endpoints.
- **Workstation Safety Interlocks (`calibration/tests.py`)**: Tests automated overdue PM detection, workstation lock toggles, and role permission validation for equipment release.
- **Material Intake & Acceptance Gating (`material_intake/tests.py`)**: Tests 10MB MTC file validation, magic-byte binary signatures (PDF, PNG, JPEG, TIFF), empty-file rejection, chemistry/mechanical conformance, open SNCR blocking, and Quality Manager exclusive batch release with audit trail persistence.
- **Dimensional Inspections (`inspection/tests.py`)**: Tests numerical tolerance calculations, `validate_measurement_value` rejection of `NaN`/`Infinity`/overflows, expired and inactive gauge lockout at model and form levels, cross-checklist item mismatch rejection, supervisor approval sign-off, post-approval edit locking, and automatic approval reset on failing readings.
- **Dispatch Clearance Gates (`inspection/tests.py`)**: Tests rejection when raw material is unaccepted or has open SNCRs, rejection when production routing operations are missing or incomplete, rejection when process hold times are unelapsed, rejection when PDI is failing or unsigned, and successful atomic release by Quality Manager or Plant Manager.

---

## 🎨 Rebuilding Tailwind CSS (Optional)

The pre-compiled CSS bundle is already committed in `static/css/tailwind.css`. If you customize templates and want to recompile:

```bash
cd factory_ops
npm install
npm run build:css
```

---

## 👤 Author & Assessment Submission

- **Candidate:** [Amarnath Bera](https://amarnathbera.in)
- **Email:** [beraamarnath5@gmail.com](mailto:beraamarnath5@gmail.com)
- **GitHub:** [@blackcoder234](https://github.com/blackcoder234)
- **Repository:** [https://github.com/blackcoder234/factory-op-qc-system](https://github.com/blackcoder234/factory-op-qc-system)
- **Demo Video:** [https://drive.google.com/file/d/1gjS2rAMI9YCtLBuhqdNpO-WHZc0bs_dZ/view?usp=sharing](https://drive.google.com/file/d/1gjS2rAMI9YCtLBuhqdNpO-WHZc0bs_dZ/view?usp=sharing)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
