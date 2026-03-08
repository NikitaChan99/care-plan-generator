# Care Plan Generator — Design Document

## 1. Overview

### 1.1 Customer

A specialty pharmacy (CVS).

### 1.2 Problem

Pharmacists spend 20–40 minutes per patient manually assembling care plans. These care plans are required for:

- **Medicare compliance** — must be on file for reimbursement
- **Pharma reporting** — required by pharmaceutical companies

The pharmacy is short-staffed and has a significant backlog.

### 1.3 Solution

A web application that allows medical assistants to input patient clinical data via a form, then automatically generate a care plan using an LLM. The generated care plan can be downloaded as a text file and printed for the patient.

### 1.4 Users

- **Medical assistants at CVS** — primary users, input data and generate care plans
- Patients do **not** interact with this system

---

## 2. Core Concepts

| Concept | Definition |
|---------|-----------|
| **Care Plan** | A clinical document tied to **one order (one medication)** for a specific patient. |
| **Order** | A single care plan request = one patient + one medication. |
| **Provider** | The referring/prescribing physician. Identified uniquely by NPI. |
| **Patient** | Identified by MRN (6-digit unique ID). |

---

## 3. Data Model

### 3.1 Input Fields

| Field | Type | Validation |
|-------|------|------------|
| Patient First Name | string | Required, non-empty |
| Patient Last Name | string | Required, non-empty |
| Referring Provider | string | Required, non-empty |
| Referring Provider NPI | string (10 digits) | Required, exactly 10 digits |
| Patient MRN | string (6 digits) | Required, exactly 6 digits, unique |
| Patient Primary Diagnosis | ICD-10 code | Required, valid ICD-10 format |
| Medication Name | string | Required, non-empty |
| Additional Diagnoses | list of ICD-10 codes | Optional, each must be valid ICD-10 format |
| Medication History | list of strings | Optional |
| Patient Records | string OR PDF file | Optional |

### 3.2 Output: Care Plan

Every generated care plan **must** contain the following four sections:

1. **Problem List / Drug Therapy Problems (DTPs)**
2. **Goals (SMART)**
3. **Pharmacist Interventions / Plan**
4. **Monitoring Plan & Lab Schedule**

---

## 4. Business Rules

### 4.1 Duplicate Detection — Orders

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| Same patient + same medication + **same day** | **ERROR** — block submission | Definite duplicate submission |
| Same patient + same medication + **different day** | **WARNING** — user can confirm and continue | Likely a refill/renewal |

### 4.2 Duplicate Detection — Patients

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| Same MRN + different name or DOB | **WARNING** — user can confirm and continue | Possible data entry error |
| Same name + same DOB + different MRN | **WARNING** — user can confirm and continue | Possibly the same person |

### 4.3 Provider Integrity

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| NPI already exists + same provider name | Auto-associate existing provider | Provider entered once |
| NPI already exists + **different** provider name | **ERROR** — must correct | NPI is a unique identifier |
| New NPI | Create new provider record | — |

**Rule: A provider is entered only once in the system, keyed by NPI.**

---

## 5. Feature Requirements

| Feature | Priority | Notes |
|---------|----------|-------|
| Web form with input validation | **Must have** | All fields validated per §3.1 |
| Patient duplicate detection | **Must have** | Cannot disrupt existing workflow |
| Order duplicate detection | **Must have** | Cannot disrupt existing workflow |
| Provider duplicate detection | **Must have** | Affects pharma reporting accuracy |
| Care plan generation (LLM) | **Must have** | Core value of the product |
| Care plan download (text file) | **Must have** | Users print and hand to patients |
| Export for pharma reporting | **Must have** | Required for pharma compliance |

---

## 6. User Workflow

```
Medical Assistant opens web form
        │
        ▼
Enters patient info, provider, medication, diagnoses, records
        │
        ▼
Form validates all inputs (real-time + on submit)
        │
        ▼
System checks for duplicate patients and orders
        │
        ├── ERROR (same patient + same med + same day) → Block, show error
        ├── WARNING (possible duplicate) → Show warning, user confirms to continue
        └── No duplicates found → Continue
        │
        ▼
System checks provider against existing records
        │
        ├── ERROR (NPI exists + name mismatch) → Block, must correct
        ├── NPI exists + name matches → Auto-associate
        └── New NPI → Create provider
        │
        ▼
Submit → Call LLM to generate care plan
        │
        ▼
Display care plan (Problem List, Goals, Interventions, Monitoring)
        │
        ▼
User downloads as text file → Prints for patient
```

---

## 7. Error Handling Strategy

### 7.1 ERROR vs WARNING

| Type | User Impact | Examples |
|------|-------------|---------|
| **ERROR** | Blocks submission, must be resolved | Same-day duplicate order; NPI/name mismatch |
| **WARNING** | User sees alert, can acknowledge and continue | Possible patient duplicate; same-med different-day |

### 7.2 Principles

- Errors are **safe, clear, and contained** — no silent failures
- Validation errors shown at the field level where possible
- Duplicate/integrity warnings shown as dismissible modals or banners
- LLM failures handled gracefully with retry option and clear messaging

---

## 8. Export / Reporting

- **Purpose:** Pharma companies require reporting on care plans generated
- **Format:** TBD (likely CSV or Excel) — confirm with customer
- **Scope:** TBD — confirm filtering options (by date range, patient, provider, medication)
- **Data:** TBD — confirm which fields are included and whether de-identification is needed

---

## 9. Production-Ready Requirements

| Requirement | Detail |
|-------------|--------|
| Input validation | Every input validated (format, required, uniqueness) |
| Data integrity | Duplicate detection and provider uniqueness enforced at all times |
| Error safety | Errors are clear, user-facing, and never leak internals |
| Modularity | Code organized into clear modules (form, validation, LLM, export) |
| Test coverage | Automated tests for validation logic, duplicate detection, provider rules |
| Zero-config startup | Project runs end-to-end out of the box |

---

## 10. Open Questions

> Items to confirm with customer before / during development.

| # | Question | Impact |
|---|----------|--------|
| 1 | What LLM provider/model to use? (OpenAI, Azure, etc.) | Architecture, cost, latency |
| 2 | Export format for pharma reporting? (CSV, Excel, PDF?) | Export feature implementation |
| 3 | Which fields to include in the pharma export? | Export feature scope |
| 4 | Patient Records as PDF — need OCR/parsing, or pass raw to LLM? | PDF handling complexity |
| 5 | Max size/page limit for uploaded PDFs? | Upload validation |
| 6 | Any HIPAA-specific hosting/encryption requirements? | Infrastructure decisions |
| 7 | Is there an existing patient/provider database to integrate with? | Data migration, integration |
| 8 | Do they need user authentication / role-based access? | Auth architecture |
| 9 | ICD-10 validation — format check only, or verify against official code list? | Validation complexity |
| 10 | Care plan text file format — plain `.txt`, or structured (`.docx`, `.pdf`)? | Output generation |

---

## 11. Example

### Input

```
Name: A.B.
MRN: 00012345
DOB: 1979-06-08 (Age 46)
Sex: Female
Weight: 72 kg
Allergies: None known
Medication: IVIG

Primary diagnosis: Generalized myasthenia gravis (G70.00), MGFA class IIb
Secondary diagnoses: Hypertension (I10), GERD (K21.0)

Home meds:
- Pyridostigmine 60 mg PO q6h PRN
- Prednisone 10 mg PO daily
- Lisinopril 10 mg PO daily
- Omeprazole 20 mg PO daily

Recent history:
Progressive proximal muscle weakness and ptosis over 2 weeks.
Neurology recommends IVIG for rapid symptomatic control.
```

### Output (Care Plan)

```
Problem List / Drug Therapy Problems (DTPs)
- Need for rapid immunomodulation to reduce myasthenic symptoms
- Risk of infusion-related reactions
- Risk of renal dysfunction or volume overload
- Risk of thromboembolic events
- Potential drug–drug interactions
- Patient education / adherence gap

Goals (SMART)
- Primary: Achieve clinically meaningful improvement in muscle strength within 2 weeks
- Safety goal: No severe infusion reaction, no acute kidney injury
- Process: Complete full 2 g/kg course with documented monitoring

Pharmacist Interventions / Plan
- Dosing & Administration
- Premedication
- Infusion rates & titration
- Hydration & renal protection
- Monitoring during infusion
- Adverse event management

Monitoring Plan & Lab Schedule
- Before first infusion: CBC, BMP, baseline vitals
- During each infusion: Vitals q15–30 min
- Post-course (3–7 days): BMP to check renal function
```
