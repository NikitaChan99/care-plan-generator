from django.core.management.base import BaseCommand

from core.models import CarePlan, Order, Patient, Provider

MOCK_PROVIDERS = [
    {"name": "Dr. Sarah Chen", "npi": "1234567890"},
    {"name": "Dr. Michael Rodriguez", "npi": "2345678901"},
    {"name": "Dr. Emily Watson", "npi": "3456789012"},
]

MOCK_PATIENTS = [
    {"first_name": "John", "last_name": "Smith", "mrn": "100001"},
    {"first_name": "Maria", "last_name": "Garcia", "mrn": "100002"},
    {"first_name": "Robert", "last_name": "Johnson", "mrn": "100003"},
    {"first_name": "Lisa", "last_name": "Anderson", "mrn": "100004"},
    {"first_name": "James", "last_name": "Wilson", "mrn": "100005"},
]

MOCK_ORDERS = [
    {
        "patient_idx": 0,
        "provider_idx": 0,
        "medication_name": "IVIG (Immune Globulin IV)",
        "primary_diagnosis": "G70.00",
        "additional_diagnoses": "I10 - Essential hypertension\nK21.0 - GERD",
        "medication_history": (
            "Pyridostigmine 60mg PO q6h PRN\n"
            "Prednisone 10mg PO daily\n"
            "Lisinopril 10mg PO daily\n"
            "Omeprazole 20mg PO daily"
        ),
        "patient_records": (
            "46F with generalized myasthenia gravis (AChR Ab+), MGFA class IIb. "
            "Progressive proximal muscle weakness and ptosis over 2 weeks. "
            "Weight 72kg, no known drug allergies, no IgA deficiency. "
            "Neurology recommends IVIG for rapid symptomatic control."
        ),
        "care_plan": """\
Problem List / Drug Therapy Problems (DTPs)
- Need for rapid immunomodulation to reduce myasthenic symptoms (ptosis, proximal weakness)
- Risk of infusion-related reactions (headache, chills, nausea)
- Risk of renal dysfunction or volume overload due to IVIG osmotic load
- Risk of thromboembolic events (DVT, PE) associated with IVIG
- Potential interaction: monitor with concurrent prednisone (immunosuppressive overlap)
- Patient education gap regarding IVIG therapy expectations and self-monitoring

Goals (SMART)
- Primary: Achieve clinically meaningful improvement in MG-ADL score (>=2-point reduction) within 2 weeks of completing IVIG course
- Safety: Zero severe infusion reactions; maintain serum creatinine within 20% of baseline
- Process: Complete full 2 g/kg IVIG course (5 daily infusions) with documented monitoring
- Adherence: Patient demonstrates understanding of hydration requirements and symptom reporting by end of first infusion

Pharmacist Interventions / Plan
- Dosing: IVIG 0.4 g/kg/day (28.8 g/day based on 72 kg) x 5 days = 144 g total
- Premedication: Acetaminophen 650 mg PO + Diphenhydramine 25 mg PO, 30 min prior
- Infusion rate: Start at 0.5 mL/kg/hr, titrate by 0.5 mL/kg/hr q30min as tolerated (max 4 mL/kg/hr)
- Hydration: Ensure adequate oral hydration (>=2L/day); pre-infusion NS 250 mL IV if renal risk
- Continue current home medications; hold lisinopril if hypotension during infusion
- Coordinate with neurology for post-course MG-ADL assessment

Monitoring Plan & Lab Schedule
- Baseline (before first infusion): CBC, BMP (Cr, BUN), LFTs, IgA level, baseline vitals
- During each infusion: Vitals (BP, HR, Temp, SpO2) q15min x 1hr, then q30min
- Daily during course: Assess for headache, rash, dyspnea, chest pain, extremity swelling
- Post-course Day 3-7: BMP (renal function check), neurology follow-up
- 2-week follow-up: MG-ADL score reassessment, determine need for repeat course""",
    },
    {
        "patient_idx": 1,
        "provider_idx": 1,
        "medication_name": "Humira (Adalimumab)",
        "primary_diagnosis": "M05.79",
        "additional_diagnoses": "E11.9 - Type 2 diabetes mellitus\nJ45.20 - Mild intermittent asthma",
        "medication_history": (
            "Methotrexate 15mg PO weekly\n"
            "Folic acid 1mg PO daily\n"
            "Metformin 1000mg PO BID\n"
            "Albuterol HFA PRN"
        ),
        "patient_records": (
            "52F with rheumatoid arthritis, inadequate response to methotrexate "
            "monotherapy after 12 weeks. DAS28 score 4.8. No prior biologic use. "
            "TB screening negative. Hepatitis B/C negative. BMI 28."
        ),
        "care_plan": """\
Problem List / Drug Therapy Problems (DTPs)
- Inadequate RA disease control on methotrexate monotherapy (DAS28 4.8)
- Risk of serious infection with TNF-alpha inhibitor initiation
- Risk of injection site reactions
- Need for tuberculosis and hepatitis monitoring with biologic therapy
- Drug interaction: adalimumab + methotrexate (intended combination, monitor hepatotoxicity)
- Diabetes management: monitor for metabolic effects

Goals (SMART)
- Primary: Achieve DAS28 score <3.2 (low disease activity) within 12 weeks
- Safety: No serious infections requiring hospitalization in first 6 months
- Process: Patient demonstrates correct self-injection technique by second dose
- Adherence: 100% on-time dosing for first 3 months (biweekly schedule)

Pharmacist Interventions / Plan
- Dosing: Adalimumab 40 mg subcutaneous injection every 2 weeks
- First dose administered in clinic with 30-min post-injection observation
- Injection training: Demonstrate proper technique (thigh or abdomen), rotation of sites
- Continue methotrexate 15 mg weekly (combination therapy per ACR guidelines)
- Ensure vaccinations up to date prior to initiation (no live vaccines on therapy)
- Provide injection calendar and missed-dose instructions

Monitoring Plan & Lab Schedule
- Baseline: CBC with differential, LFTs, BMP, TB screen (QuantiFERON), Hep B/C panel
- Week 4: Phone follow-up — assess injection technique, side effects, early response
- Week 8: CBC, LFTs (hepatotoxicity with MTX combination)
- Week 12: Rheumatology visit, DAS28 reassessment, CBC, LFTs, BMP
- Ongoing: LFTs every 3 months, annual TB screening, infection monitoring""",
    },
    {
        "patient_idx": 2,
        "provider_idx": 2,
        "medication_name": "Remicade (Infliximab)",
        "primary_diagnosis": "K50.90",
        "additional_diagnoses": "K50.012 - Crohn's with rectal bleeding\nD50.9 - Iron deficiency anemia",
        "medication_history": (
            "Mesalamine 1.2g PO TID\n"
            "Iron sulfate 325mg PO daily\n"
            "Azathioprine 150mg PO daily"
        ),
        "patient_records": (
            "34M with Crohn's disease, moderate-to-severe flare. Colonoscopy shows "
            "active ileocolonic inflammation. Failed conventional therapy. "
            "Fistulizing phenotype suspected. BMI 22. Weight 70kg."
        ),
        "care_plan": """\
Problem List / Drug Therapy Problems (DTPs)
- Active moderate-to-severe Crohn's disease refractory to conventional therapy
- Risk of infusion reactions (acute and delayed) with infliximab
- Risk of serious/opportunistic infections with anti-TNF therapy
- Iron deficiency anemia requiring ongoing monitoring, possible IV iron
- Drug interaction: azathioprine + infliximab (intentional combo; monitor lymphoma risk)
- Risk of hepatotoxicity with combination immunosuppression

Goals (SMART)
- Primary: Achieve clinical remission (CDAI <150) by Week 14 (after 3 induction doses)
- Safety: No infusion reactions requiring treatment discontinuation
- Lab: Hemoglobin improvement to >11 g/dL within 8 weeks
- Mucosal: Endoscopic evidence of mucosal healing at 6-month reassessment

Pharmacist Interventions / Plan
- Induction: Infliximab 5 mg/kg IV at Weeks 0, 2, and 6 (350 mg per dose)
- Maintenance: 5 mg/kg IV every 8 weeks starting Week 14
- Premedication: Acetaminophen 650mg + Diphenhydramine 50mg + Hydrocortisone 100mg IV
- Infusion: Administer over >=2 hours; observe 1 hour post-infusion
- Continue azathioprine 150 mg daily (reduces immunogenicity)
- Assess iron status; recommend IV iron (Venofer) if oral insufficient after 4 weeks

Monitoring Plan & Lab Schedule
- Baseline: CBC, CMP, LFTs, CRP, ESR, fecal calprotectin, TB screen, Hep B/C
- Before each infusion: CBC, LFTs, CRP
- Week 6 (before 3rd induction): CDAI assessment, hemoglobin, fecal calprotectin
- Week 14: Full labs, clinical response assessment, GI follow-up
- Every 8 weeks (maintenance): CBC, LFTs, CRP, infliximab trough if loss of response
- 6 months: Colonoscopy for mucosal healing assessment""",
    },
    {
        "patient_idx": 3,
        "provider_idx": 0,
        "medication_name": "Ocrevus (Ocrelizumab)",
        "primary_diagnosis": "G35",
        "additional_diagnoses": "F32.1 - Major depressive disorder\nG43.909 - Migraine, unspecified",
        "medication_history": (
            "Tecfidera 240mg PO BID (discontinuing)\n"
            "Sertraline 100mg PO daily\n"
            "Sumatriptan 50mg PO PRN"
        ),
        "patient_records": (
            "38F with relapsing-remitting MS, 2 relapses in past year despite "
            "dimethyl fumarate. MRI shows 3 new T2 lesions. EDSS 2.5. "
            "Switching to higher-efficacy therapy. JCV antibody negative. Weight 65kg."
        ),
        "care_plan": """\
Problem List / Drug Therapy Problems (DTPs)
- Breakthrough MS activity on dimethyl fumarate (2 relapses, new MRI lesions)
- Risk of infusion-related reactions with ocrelizumab (especially first dose)
- Risk of infection due to B-cell depletion (PML, respiratory infections)
- Hepatitis B reactivation risk with anti-CD20 therapy
- Need for vaccination review prior to B-cell depletion
- Concurrent depression management — monitor for MS-related mood changes

Goals (SMART)
- Primary: No new relapses or MRI activity (NEDA-3) at 12-month reassessment
- Safety: No Grade 3+ infusion reactions; no serious infections in first year
- Process: Complete first full dose (two 300 mg infusions) within 14 days
- Transition: Successful washout from dimethyl fumarate (>=4 weeks, ALC recovery)

Pharmacist Interventions / Plan
- Washout: Confirm dimethyl fumarate discontinued >=4 weeks; check ALC >800/uL
- First dose: Split — 300 mg IV Day 1, 300 mg IV Day 15
- Subsequent doses: 600 mg IV every 6 months
- Premedication: Methylprednisolone 100mg IV + Acetaminophen 650mg + Diphenhydramine 50mg
- Infusion rate: Start 30 mL/hr, increase by 30 mL/hr q30min (max 180 mL/hr)
- Ensure vaccinations completed >=6 weeks before first dose (no live vaccines on therapy)

Monitoring Plan & Lab Schedule
- Baseline: CBC with differential (ALC), immunoglobulins (IgG, IgM), HBV panel, JCV Ab, LFTs
- Pre-each infusion: CBC, immunoglobulin levels
- During infusion: Vitals q15min x 1hr, then q30min; monitor for flushing, hypotension
- Every 6 months: MRI brain/spine, EDSS assessment, CBC, immunoglobulins
- Annually: JCV antibody retest, dermatologic screening, vaccination review""",
    },
    {
        "patient_idx": 4,
        "provider_idx": 1,
        "medication_name": "Keytruda (Pembrolizumab)",
        "primary_diagnosis": "C34.90",
        "additional_diagnoses": (
            "J44.1 - COPD with acute exacerbation\n"
            "I48.91 - Atrial fibrillation\n"
            "E78.5 - Hyperlipidemia"
        ),
        "medication_history": (
            "Carboplatin/Pemetrexed (completed 4 cycles)\n"
            "Apixaban 5mg PO BID\n"
            "Atorvastatin 40mg PO daily\n"
            "Tiotropium 18mcg INH daily\n"
            "Albuterol HFA PRN"
        ),
        "patient_records": (
            "67M with stage IIIB NSCLC adenocarcinoma. PD-L1 TPS 80%. "
            "Completed 4 cycles carboplatin/pemetrexed with partial response. "
            "Transitioning to pembrolizumab maintenance. ECOG 1. "
            "No autoimmune history. Weight 78kg."
        ),
        "care_plan": """\
Problem List / Drug Therapy Problems (DTPs)
- Need for maintenance immunotherapy after initial chemotherapy response
- Risk of immune-mediated adverse events (pneumonitis, colitis, hepatitis, endocrinopathies)
- Risk of pneumonitis particularly concerning given baseline COPD
- Drug interaction: apixaban with potential pembrolizumab hepatotoxicity
- COPD exacerbation management alongside immunotherapy
- Atrial fibrillation anticoagulation management during cancer treatment

Goals (SMART)
- Primary: Maintain disease control (stable/continued partial response) at 12-week CT
- Safety: No Grade 3+ immune-mediated adverse events in first 6 months
- Pulmonary: Maintain FEV1 within 10% of baseline; no treatment-related pneumonitis
- Process: Complete first 4 cycles (12 weeks) of maintenance without dose delays

Pharmacist Interventions / Plan
- Dosing: Pembrolizumab 200 mg IV every 3 weeks (flat dose)
- Infusion: Administer over 30 minutes; no standard premedication required
- Monitor thyroid function closely — most common endocrinopathy with PD-1 inhibitors
- Hold pembrolizumab and initiate high-dose steroids if Grade 2+ pneumonitis
- Continue apixaban; monitor LFTs closely (shared hepatic concerns)
- COPD action plan: Ensure rescue inhaler available; low threshold for pulmonary consult
- Provide irAE wallet card; instruct to report new cough, diarrhea, rash, fatigue

Monitoring Plan & Lab Schedule
- Before each cycle (q3w): CBC, CMP, LFTs, TSH, free T4, urinalysis
- Baseline and every 6 weeks: Chest X-ray (pneumonitis screening vs COPD)
- Week 12: CT chest/abdomen/pelvis (RECIST response assessment)
- Every 6 weeks: Oncology assessment, ECOG status, symptom review
- As needed: PFTs if new respiratory symptoms; cortisol if fatigue worsens
- Ongoing: irAE monitoring — new organ-specific symptoms trigger targeted workup""",
    },
]


class Command(BaseCommand):
    help = "Seed database with mock providers, patients, orders, and care plans"

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing data...")
        CarePlan.objects.all().delete()
        Order.objects.all().delete()
        Patient.objects.all().delete()
        Provider.objects.all().delete()

        self.stdout.write("Creating providers...")
        providers = [Provider.objects.create(**p) for p in MOCK_PROVIDERS]

        self.stdout.write("Creating patients...")
        patients = [Patient.objects.create(**p) for p in MOCK_PATIENTS]

        self.stdout.write("Creating orders and care plans...")
        for od in MOCK_ORDERS:
            care_plan_text = od.pop("care_plan")
            od["patient"] = patients[od.pop("patient_idx")]
            od["provider"] = providers[od.pop("provider_idx")]
            order = Order.objects.create(**od)
            CarePlan.objects.create(order=order, content=care_plan_text)

        self.stdout.write(self.style.SUCCESS(
            f"Done! {Provider.objects.count()} providers, "
            f"{Patient.objects.count()} patients, "
            f"{Order.objects.count()} orders with care plans."
        ))
