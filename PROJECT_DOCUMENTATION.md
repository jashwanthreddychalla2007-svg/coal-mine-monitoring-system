# KhananRakshak (CoalGuard AI) - Comprehensive Project Master Document

---

## 1. Deconstructing the Problem Statement in Simple Words

### The Real-World Background
India is one of the largest coal producers in the world. Operations are managed primarily by **Coal India Limited (CIL)** through massive subsidiary companies spread across various states:
- **BCCL** (Bharat Coking Coal Ltd - Dhanbad, Jharkhand)
- **ECL** (Eastern Coalfields Ltd - West Bengal & Jharkhand)
- **CCL** (Central Coalfields Ltd - Ranchi, Jharkhand)
- **SECL** (South Eastern Coalfields Ltd - Chhattisgarh & MP)
- **WCL** (Western Coalfields Ltd - Maharashtra & MP)
- **MCL** (Mahanadi Coalfields Ltd - Odisha)
- **NCL** (Northern Coalfields Ltd - Singrauli, MP/UP)

Mining coal is **dangerous, heavily regulated, and massive in scale**. Every single day, hundreds of mines operate under strict laws set by:
1. **DGMS (Directorate General of Mines Safety)** under the *Mines Act 1952* and *Coal Mines Regulations (CMR) 2017*.
2. **MoEFCC & CPCB (Ministry of Environment, Forest and Climate Change / Central Pollution Control Board)** for dust, air quality, deforestation, and water discharge limits.
3. **Labour Ministry** for safety training of contractual dumper drivers, miners, and medical examinations.

### The Pain Point: What is Going Wrong Today?
Right now, coal mining governance in India is **fragmented and manual**:
- Safety officers write observations in paper logbooks or disparate spreadsheets.
- When an inspector finds a dangerous condition (e.g., toxic methane gas buildup or unstable mine pit slope), the report takes days or weeks to travel through bureaucracy to the General Manager or DGMS headquarters.
- Private contractor agencies bring thousands of contractual workers into the pits, many without proper safety certifications (VTC) or expired insurance.
- Corporate headquarters in Kolkata or New Delhi only receives delayed, summarized monthly reports. They have no real-time visibility into which mine is about to have a disaster.

### What the Problem Statement Demands
The Ministry and Hackathon judges want **one single centralized, digital, AI-powered system** that connects:
1. **Corporate Headquarters & Regulators** (macro visibility).
2. **Colliery & Mine Managers** (operational tracking & statutory deadlines).
3. **Field Safety Officers in the Pit** (geo-tagged mobile audits with GPS and photos).
4. **AI & Machine Learning Engine** (analyzes gas sensor readings, overdue compliance, and flags high-risk mines before disasters occur).

---

## 2. Complete Technical Stack

| Layer | Technologies Used | Why It Was Chosen |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.13 + FastAPI** | Extremely fast, native async support, handles heavy data loads, auto-generates interactive Swagger documentation (`/docs`), and enables seamless integration with Python AI/ML libraries. |
| **Server Runtime** | **Uvicorn (ASGI)** | High-performance production-ready server capable of handling asynchronous requests. |
| **AI / Risk Algorithm** | **Custom Multi-Factor Probabilistic Scoring Engine** | Evaluates statutory compliance delays, environmental sensor telemetry ($CH_4, CO, PM_{10}$), active violations, and historical safety records to generate the **Mine Risk Index (MRI)**. |
| **Data Validation** | **Pydantic v2** | Strict data modeling, input sanitization, and type safety for API requests and database models. |
| **Frontend UI** | **Vanilla HTML5 + Semantic CSS3** | Clean, responsive, official Indian Government portal aesthetic (Navy Blue `#0b3954` / Off-white `#f4f6f9`), zero bulky dependencies, runs natively in any browser with instant load times. |
| **Interactive Charts** | **Chart.js v4** | Lightweight operational bar graphs comparing compliance percentages across subsidiaries. |
| **GIS Geospatial Mapping** | **Leaflet.js + OpenStreetMap** | Open-source geospatial visualization plotting exact GPS coordinates of coal pits across India with dynamic color-coded hazard markers. |
| **Version Control** | **Git** | Standardized repository structure ready for GitHub push and team collaboration. |

---

## 3. Dissecting the Platform: Feature-by-Feature & Button-by-Button

The application runs at `http://127.0.0.1:8000` and is divided into **6 functional modules** accessible via the top navigation bar.

---

### Top Navigation & Identity Bar
- **Government Identity Topbar**: Shows "Government of India | Ministry of Coal | Coal India Limited (CIL)" along with the official tricolor strip.
- **Filter Subsidiary Dropdown**:
  - Located in the top right.
  - Allows officials to filter the entire portal by subsidiary (e.g., BCCL, ECL, SECL) or view the entire country ("All Subsidiaries").
- **Portal User Indicator**: Displays role-based context (`DGMS Inspector / CIL HQ`).

---

### Tab 1: Executive Dashboard (Macro HQ View)
**Target Users:** Chairman & Directors of Coal India Limited, Ministry of Coal Officials, Chief Inspector of Mines (DGMS).

#### 1. KPI Summary Cards (Top Row)
- **Mines Monitored**: Total number of coal mines currently transmitting data into the digital system.
- **National Statutory Index**: The country-wide average compliance percentage across all statutory mandates (Mines Act, CMR 2017).
- **Overdue Statutory Items**: Highlights the exact count of legal safety requirements that have passed their mandatory completion deadline.
- **High-Risk Mine Sites**: Displays how many mines have reached critical hazard status based on AI risk scoring.

#### 2. Subsidiary Compliance Index (Bar Chart)
- Visualizes and ranks each subsidiary (BCCL, ECL, SECL, MCL, NCL) based on their safety compliance record.
- **Color Logic**:
  - Green ($\ge 90\%$): Strong compliance.
  - Amber ($80-89\%$): Warning / Needs improvement.
  - Red ($< 80\%$): Non-compliant / Inspection required.

#### 3. Statutory Escalations Panel
- Shows active safety violations where the colliery failed to rectify the issue within the prescribed SLA (Service Level Agreement).
- **Automated Escalation**: When an inspector flags a dangerous "Class A" issue and the mine does not fix it, the system automatically marks it as `Auto-escalated to General Manager due to SLA breach`.

#### 4. Monitored Mine Operations Registry (Table)
- Lists each active colliery (e.g., Jharia Block IV, Moonidih Deep Underground, Gevra Mega Opencast, Kusmunda, Rajmahal).
- Displays real-time daily output (Metric Tonnes) vs target.
- Shows live telemetry:
  - For **Underground Mines**: Methane ($CH_4\%$) and Carbon Monoxide ($CO\text{ ppm}$).
  - For **Opencast Mines**: Suspended dust levels ($PM_{10}\ \mu\text{g/m}^3$).
- Displays the real-time AI Risk Score.
- **"Refresh Data" Button**: Re-queries the backend API to fetch the latest sensor feeds and compliance counts.
- **"View Details" Button on any mine row**: Immediately switches the user to the **AI Risk & Anomaly Assessment** tab focused on that specific colliery.

---

### Tab 2: GIS Spatial Map (Geographic Surveillance)
**Target Users:** Surveyors, Environmental Officers, Central Disaster Control Rooms.

- **What it does**: Renders a satellite/topographic interactive map of India centered over the prime coal mining belts (Jharkhand, West Bengal, Odisha, Chhattisgarh, MP).
- **Interactive Markers**:
  - Each coal mine is plotted at its true latitude and longitude.
  - **Color Coding**:
    - 🔴 **Red Marker**: High Risk / Hazard threshold exceeded (e.g., Moonidih Underground with $0.65\%\ CH_4$).
    - 🟡 **Amber Marker**: Elevated risk / Overdue compliance items.
    - 🟢 **Green Marker**: Safe and fully compliant.
- **Clicking any Marker**:
  - Opens a clean informational popup displaying the colliery name, subsidiary, operation type (Opencast vs Underground), AI risk score, and real-time gas/dust readings.

---

### Tab 3: Statutory Compliance Register (Legal & Regulatory Engine)
**Target Users:** Colliery Managers, Mine Safety Officers, DGMS Regulatory Inspectors.

- **What it does**: Digitizes statutory compliance registers that were historically maintained in physical logbooks under the *Mines Act 1952* and *Coal Mines Regulations 2017*.
- **Filter Buttons**:
  - **"All Records"**: Shows the complete compliance inventory.
  - **"Overdue"**: Filters down to items that have breached their deadline (e.g., Reg 169 Gas Telemetry overdue).
  - **"Pending"**: Shows upcoming inspections and audits that must be completed soon.
  - **"Complied"**: Shows fulfilled mandates.
- **"Verify" Action Button**:
  - Next to any non-complied item, an inspector can click **"Verify"**.
  - This immediately triggers an API request to the backend (`/api/compliances/{id}/update-status`), timestamps the official closure, updates the status to **Complied**, and recalculates the national compliance percentage in real time.

---

### Tab 4: Field Inspection & Audit (Geo-Tagged Reporting)
**Target Users:** Field Safety Officers and DGMS Inspectors walking inside the mine pit.

#### The Submission Form (Left Side):
- **Select Mine / Colliery Dropdown**: Chooses which mine is being audited.
- **Inspector Name & Designation**: Captures who is conducting the inspection.
- **Audit Type Dropdown**: Selects whether it is a daily ventilation check, a surprise statutory audit, bench stability audit, or environmental check.
- **Violation Classification Dropdown**:
  - *Class A*: Life Threatening (Triggers automatic instant escalation).
  - *Class B*: Major Operational Non-Compliance.
  - *Class C*: Minor Observational Defect.
- **Observations & Findings**: Text area where the officer details exact hazards observed in the field.
- **Corrective Action Prescribed**: Text area where mandatory rectification instructions and SLA timelines are recorded.
- **GPS Coordinates Field**: Simulates the mobile device's GPS lock (`23.7438, 86.4116`). This prevents "desk inspections" where officers fill reports without actually visiting the pit.
- **Evidence Document / Image Link**: Attaches photo proof of the hazard.
- **"Submit Inspection Report" Button**:
  - Validates the form data.
  - Sends a `POST` request to the backend API.
  - Automatically re-evaluates the mine's risk level (if a Class A violation is logged, the mine is instantly downgraded to High Risk).
  - Prepends the report to the audit trail on the right.

#### Recent Inspection Log (Right Side):
- Displays time-stamped cards of every audit logged across the coalfields, showing inspector details, GPS coordinates, violation category, and prescribed remedies.

---

### Tab 5: AI Risk & Anomaly Assessment (Predictive Intelligence)
**Target Users:** General Managers, Safety Directors, Technical Auditors.

- **What it does**: Shows the output of our AI risk engine for each mine. Instead of waiting for an accident to happen, the AI continuously computes a **Mine Risk Index (MRI)** from 0 to 100.
- **What each card displays**:
  - **MRI Score Badge**: e.g., `Score: 73.0 / 100` (High Risk).
  - **Statistical Hazard Probability**: Machine learning calculated probability of a safety incident occurring in the next 30 days if conditions remain unaddressed.
  - **Contributing Risk Factors**: Explains *why* the score is high (e.g., *"Elevated Methane (0.65%) approaching statutory threshold"*, *"Class-A Statutory requirement is OVERDUE"*).
  - **Prescribed Compliance Action**: Automated AI recommendations (e.g., *"Increase auxiliary ventilation air velocity to minimum 0.5 m/s"*, *"Urgent DGMS clearance submission required"*).
  - **Operational / Environmental Clearance Anomaly Alert**: Flags when a mine's daily extraction rate threatens to breach the annual MoEFCC Environmental Clearance ceiling or when an unexpected production drop indicates an unrecorded operational failure.

---

### Tab 6: Contractor Compliance (Outsource Agency Governance)
**Target Users:** Personnel Officers, Vigilance Officers, Labour Commissioners.

- **What it does**: A huge portion of coal mining (transportation, heavy machinery operation, overburden removal) is outsourced to private contractors. This tab tracks whether these third-party companies adhere to safety laws.
- **Columns Tracked**:
  - **Agency ID & Contractor Name**: e.g., *BEEPC Mining Services Ltd.*, *Vindhya Earthmovers*.
  - **Allocated Mine Project**: Which mine site they are operating in.
  - **Deployed Manpower**: Number of workers inside the active mining zone.
  - **Safety Audit Score**: Percentage score from recent third-party audits.
  - **Certified Operators**: Tracks whether heavy equipment operators have mandatory **Vocational Training (VTC)** certification under the Mines Vocational Training Rules 1966.
  - **Insurance Validity**: Alerts if the contractor's mandatory workmen compensation, ESI, or EPF coverage is nearing expiry.
  - **Regulatory Status & Risk Evaluation**: Flags contractors that are high risk before their unsafe machinery or untrained drivers cause fatal haul road accidents.

---

## 4. How to Explain This Project to SIH Judges (Elevator Pitch)

> *"Respected Judges, the Indian coal mining sector produces over 900 million tonnes of coal annually, but governance and compliance monitoring across subsidiaries like BCCL, ECL, and SECL are plagued by manual paperwork, delayed incident reporting, and compliance blind spots.*
> 
> *Our solution, **KhananRakshak**, is a centralized, AI-enabled governance platform designed specifically for the Ministry of Coal, DGMS, and Coal India.*
> 
> *Key highlights:*
> 1. *It replaces fragmented registers with a digital **Statutory Compliance Register** covering the Mines Act 1952 and CMR 2017.*
> 2. *It equips field inspectors with **Geo-Tagged, Time-Stamped Auditing** that locks GPS coordinates and photos to prevent falsified reports.*
> 3. *Our **AI Risk Engine** evaluates live gas telemetry ($CH_4, CO$), dust levels, and overdue compliance to compute a real-time **Mine Risk Index (MRI)**, alerting leadership to hazards before accidents happen.*
> 4. *It provides a nationwide **GIS Spatial Map** and **Contractor Governance Module** to track outsourced machinery and labour certifications.*
> 5. *Built with a clean, official light portal aesthetic and high-performance Python FastAPI backend, it is lightweight, secure, and ready for national deployment."*
