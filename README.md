# 🏭 Factory Operations & Quality Control System (FactoryOps QC)

> **Zapuza Technologies LLP — Python Django Developer Internship Online Assessment**  
> An enterprise-grade shopfloor quality management and machine tracking web application built with **Python 3.10+** and **Django 5.x**.

---

## 📌 Project Overview

In modern manufacturing facilities, reliance on paper-based inspection sheets, physical logbooks, and fragmented spreadsheets leads to quality escapes, overdue machine operations, and untraceable non-conformances.

**FactoryOps QC** digitizes the entire shopfloor workflow into a unified, audit-compliant web application covering the 4 core quality pillars:

1. **Master Factory Infrastructure Setup:** Comprehensive registers for Departments, Machine Workstations, Manufactured Components/Parts, and Inspection Gauges with automatic calibration due tracking.
2. **Machine Calibration & Workstation Safety Lock:** Enforces preventive maintenance schedules; automatically detects overdue equipment and disables job selection/measurements to prevent out-of-spec production.
3. **Raw Material Intake & Mill Test Certificate (MTC) Verification:** Dock receiving workflow logging Heat Numbers, Purchase Orders, chemical composition tolerances (C, Mn, Si, etc.), mechanical properties (tensile strength, hardness), and Supplier Non-Conformance (SNCR) quarantine flows.
4. **Pre-Dispatch Inspection (PDI) Checklists & Measurement Validation:** Template design studio defining upper/lower dimensional tolerances (e.g., $50.00 \pm 0.02\text{ mm}$) with real-time automated **PASS/FAIL** evaluation upon measurement entry.

---

## 🏗️ Architecture & Modules

The project is structured into modular, decoupled Django applications:

```text
factory_ops/
│
├── manage.py
│
├── factory_ops/             # Project Configuration (settings, urls, wsgi)
│
├── master_setup/            # Module 1: Departments, Machines, Parts, Gauges
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── calibration/             # Module 2: Maintenance Records, Machine Lock Logic
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── material_intake/         # Module 3: Heat Nos, MTC Chemistry/Mechanics, SNCR
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
└── inspection/              # Module 4: Checklists, Tolerance Engine, Auto Pass/Fail
    ├── models.py
    ├── views.py
    ├── forms.py
    └── urls.py
```

---

## 🛠️ Technology Stack

- **Backend:** Python 3.10+ / Django 5.x
- **Database:** SQLite (default for development)
- **Frontend:** Django Template Engine (DTL), HTML5, CSS3, Bootstrap 5 / Modern Responsive UI
- **File Uploads:** Django `FileField` for Mill Test Certificates (PDF)
- **Security:** CSRF Protection, Django Authentication, Input Validation

---

## 🚀 Getting Started (Run Locally)

### 1. Prerequisites

- Python 3.10 or higher
- Git

### 2. Clone the Repository

```bash
git clone https://github.com/<your-username>/zapuza-factory-ops.git
cd zapuza-factory-ops
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

### 5. Apply Database Migrations

```bash
cd factory_ops
python manage.py migrate
```

### 6. Create Superuser (Admin Access)

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit the application in your browser:

- **Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🎥 Video Walkthrough & Demo

- **Video Demo Link:** [Insert your Loom / YouTube link here]
  _(A comprehensive screen recording with voice narration explaining the code architecture, models, and a live demonstration of all 4 modules)._

---

## 📄 Documentation

Detailed technical specifications, architecture diagrams, interview Q&A defense, and the LaTeX source guide are available in the [`docs/`](docs/) folder.

---

## 👤 Author

- **Name:** Amarnath Bera
- **Role:** Python Django Developer Intern Candidate
- **Company:** Zapuza Technologies LLP
