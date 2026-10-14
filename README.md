<div align="center">

# 🏭 Factory Operations & Quality Control System (FactoryOps QC)

### Enterprise Shopfloor Quality Management & Interlock Safety Platform
Built for **Zapuza Technologies LLP** — Python Django Developer Internship Assessment

[![Django](https://img.shields.io/badge/Django-5.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4.0-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Complete-emerald?style=for-the-badge)](#)

</div>

---

## 📌 Executive Summary

In precision manufacturing facilities, paper logbooks and manual inspection sheets lead to quality escapes, overdue machine tool operations, and untraceable metallurgical deviations.

**FactoryOps QC** digitizes the entire shopfloor quality lifecycle into a unified, audit-compliant web application covering the 4 core quality pillars specified in the Business Requirements Document (BRD v5.0):

<table>
  <tr>
    <td width="30%">🏭 <b>Module 1: Master Setup</b></td>
    <td>Registers factory departments, CNC machine tools, manufactured parts (with drawing numbers and revisions), and precision gauges with calibration due tracking.</td>
  </tr>
  <tr>
    <td>🔒 <b>Module 2: Calibration & Lock</b></td>
    <td>Enforces preventive maintenance (PM) schedules; automatically detects overdue equipment and disables job selection/measurements to prevent out-of-spec production.</td>
  </tr>
  <tr>
    <td>📦 <b>Module 3: Material Intake & MTC</b></td>
    <td>Dock receiving workflow logging Heat Numbers, Purchase Orders, chemical composition tolerances (C, Mn, Si, P, S), mechanical properties (UTS, YS, Hardness), and Supplier Non-Conformance (SNCR) quarantine flows.</td>
  </tr>
  <tr>
    <td>📐 <b>Module 4: PDI Checklists</b></td>
    <td>Inspection template design studio defining nominal dimensions and tolerances (e.g., $50.00 \pm 0.02\text{ mm}$) with real-time automated <b>PASS / FAIL</b> evaluation upon measurement entry.</td>
  </tr>
</table>

---

## 🏗️ Architecture & Decoupled Apps

The system follows Django's clean modular architecture with 4 independent feature applications:

```text
factory-op-qc-system/
│
├── factory_ops/                     # Django Project Root
│   ├── manage.py                    # Django CLI Management Tool
│   ├── package.json                 # Tailwind CSS v4 compiler config
│   │
│   ├── factory_ops/                 # Master Configuration (settings.py, urls.py, wsgi.py)
│   ├── master_setup/                # Module 1: Departments, Machines, Parts, Gauges
│   ├── calibration/                 # Module 2: Maintenance Records, Machine Lock Logic
│   ├── material_intake/             # Module 3: Heat Nos, MTC Chemistry & Mechanics, SNCR
│   ├── inspection/                  # Module 4: Checklists, Tolerance Engine, Auto Pass/Fail
│   │
│   ├── templates/                   # Tailwind CSS v4 DTL templates
│   ├── static/                      # Compiled CSS (tailwind.css, custom.css)
│   └── media/                       # Uploaded MTC documents & certificates
│
├── requirements.txt                 # Pinned Python package dependencies
├── .gitignore                       # Clean Git exclusion rules
├── LICENSE                          # MIT Open Source License
└── README.md                        # Documentation & setup guide
```

---

## 🛠️ Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend Framework** | **Python 3.10+ / Django 5.x** | Batteries-included, ORM, CSRF protection, admin panel |
| **Styling & UI** | **Tailwind CSS v4 + Vanilla CSS** | Enterprise dark-mode design, responsive tables, zero CDN latency |
| **Typography** | **Plus Jakarta Sans & JetBrains Mono** | Modern enterprise feel with legible numerical measurements |
| **Database** | **SQLite (Dev) / PostgreSQL Ready** | Zero-config local development with atomic transaction safety |
| **File Storage** | **Django FileField** | Upload and archive Mill Test Certificates (PDF) |
| **Version Control** | **Git & GitHub** | Clean commit history and branch management |

---

## 🚀 Getting Started (Run Locally)

### 1. Prerequisites
* Python 3.10 or higher
* Git

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

### 5. Apply Database Migrations
```bash
cd factory_ops
python manage.py migrate
```

### 6. Populate Realistic Demo Data (Optional but Recommended)
Populates realistic factory bays, machines, calibrated gauges, steel heat batches, and PDI checklists:
```bash
python manage.py seed_data
```

### 7. Create Superuser (Admin Access)
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```

Visit the application in your browser:
* **Plant Overview Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Workstation Lock Board:** [http://127.0.0.1:8000/calibration/](http://127.0.0.1:8000/calibration/)
* **Raw Material Intake & MTC:** [http://127.0.0.1:8000/materials/](http://127.0.0.1:8000/materials/)
* **PDI Inspection Sheet:** [http://127.0.0.1:8000/inspection/records/1/](http://127.0.0.1:8000/inspection/records/1/)
* **Django Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🎨 Rebuilding CSS (Optional)

The pre-compiled CSS bundle is already committed in `static/css/tailwind.css`, so **no Node.js build step is required** to run the app. If you modify template classes and wish to recompile:

```bash
cd factory_ops
npm install
npm run build:css
```

---

## 🎥 Video Walkthrough & Demo

* **Video Walkthrough Link:** [Insert your Loom / YouTube demo video link here]  
  *(A comprehensive screen recording with voice narration explaining the code architecture, models, and a live demonstration of all 4 modules).*

---

## 👤 Author

* **Developer:** [Amarnath Bera](https://amarnathbera.in)
* **Contact:** [beraamarnath5@gmail.com](mailto:beraamarnath5@gmail.com)
* **GitHub:** [@blackcoder234](https://github.com/blackcoder234)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
