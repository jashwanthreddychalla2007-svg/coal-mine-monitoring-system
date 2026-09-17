# ⛏️ KhananRakshak (CoalGuard AI)
### AI-Based Smart Governance and Compliance Monitoring System for Coal Mines
**Smart India Hackathon (SIH)**

---

## 📌 Problem Overview
The Indian coal mining sector involves large-scale operations spread across multiple subsidiaries (CIL: BCCL, ECL, CCL, WCL, SECL, MCL, NCL, CMPDI), mine sites, contractors, regulatory bodies (DGMS, MoEFCC, CPCB), and field offices. Governance-related activities such as statutory compliance monitoring, inspection tracking, safety observations, production reporting, environmental monitoring, worker attendance, and contract management are traditionally managed through fragmented systems and manual paperwork.

**KhananRakshak** is an indigenous, integrated digital e-governance platform powered by AI risk modeling, GIS satellite spatial analysis, automated statutory escalation workflows, and geo-tagged field auditing.

---

## 🚀 Key Features

1. **🏛️ Centralized Multi-Tier Governance Dashboard**:
   - **Corporate HQ (CIL / Ministry)**: National compliance index (%), subsidiary rankings, real-time safety KPIs.
   - **Colliery / Mine Level**: Shift logs, safety checklist, statutory register (Mines Act 1952, CMR 2017).
   - **DGMS Regulatory Inspectorate**: Violation notices, statutory penalties, and SLA tracking.

2. **🧠 AI Predictive Risk & Anomaly Engine**:
   - **Mine Risk Index (MRI)**: Composite safety score factoring live telemetry (Methane $CH_4$, Carbon Monoxide $CO$, Dust $PM_{10}$), overdue statutory actions, and active violations.
   - **Production vs. Environmental Clearance (EC) Anomaly Detection**: Flags over-extraction risks and severe operational bottlenecks.
   - **Prescriptive AI Interventions**: Automated recommendations to mitigate hazards before accidents occur.

3. **🗺️ Interactive GIS Spatial Risk Map**:
   - Leaflet-based geospatial mapping plotting open-cast and underground mines across India with dynamic risk color markers.

4. **📍 Geo-Tagged & Time-Stamped Field Inspection (Mobile PWA Ready)**:
   - Captures GPS coordinates, timestamps, inspector signatures, and audit photo evidence.
   - Auto-escalates **Class A (Life Threatening)** violations to the General Manager if SLA expires.

5. **👷 Contractor & Labour Compliance Module**:
   - Tracks safety audit scores, Vocational Training (VTC) operator certifications, and statutory insurance (ESI/EPF) validity.

---

## 🛠️ Tech Stack

- **Backend**: Python FastAPI, Uvicorn, Pydantic
- **AI/ML Engine**: Multi-factor probabilistic risk scoring & anomaly detection algorithms
- **Frontend**: Responsive Single Page Application (SPA) with Dark Slate / Coal Amber theme, Chart.js operational charts, Leaflet GIS mapping
- **API Documentation**: Auto-generated Swagger UI (`/docs`)

---

## 🏃 How to Run the Project Locally

### 1. Prerequisites
- Python 3.10+ installed

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the Server
```powershell
python run.py
```
Or:
```powershell
uvicorn backend.main:app --reload --port 8000
```

### 4. Access the Platform
- **Web Application**: Open [http://localhost:8000](http://localhost:8000) in your browser.
- **Interactive REST API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 👥 How to Collaborate with Your Team

1. **Push to GitHub**:
   ```powershell
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git branch -M main
   git push -u origin main
   ```
2. **Invite Teammates**:
   - Add your teammates as collaborators on GitHub.
   - They can clone the repository:
     ```bash
     git clone https://github.com/<your-username>/<your-repo-name>.git
     cd <your-repo-name>
     pip install -r requirements.txt
     python run.py
     ```
3. **Live Pair Programming**:
   - You can also use **VS Code / IDE Live Share** (`Ctrl + Shift + P` -> `Live Share: Start Collaboration Session`) to work together in real-time.
