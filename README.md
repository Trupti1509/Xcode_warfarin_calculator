# Xcode Life Warfarin Dosing Calculator (V1.3.1 Scientific Release)

A scientifically rigorous, clinically grounded Warfarin Pharmacogenetic (PGx) and Clinical Dosing Calculator implementing the published algorithms of the **International Warfarin Pharmacogenetics Consortium (IWPC)**, layered with **Clinical Pharmacogenetics Implementation Consortium (CPIC) 2017** guidelines and **U.S. FDA Warfarin prescribing information**.

---

## 1. Scientific Scope & Core Principles

1. **Target Population & Scope**:
   - Adult patients (aged 18–120 years).
   - Target INR of **2.0–3.0**.
   - Estimates an expected **stable maintenance dose** in mg/week (and average daily equivalent in mg/day).
   - **Not an INR-based dose-adjustment tool** and **does not calculate a loading regimen**.
2. **Point Estimates (No Invented Safe Ranges)**:
   - Displays the calculated IWPC point estimate (`XX.X mg/week` and `X.X mg/day`).
   - The IWPC paper's ±20% metric was an algorithm accuracy measure, not an individualized therapeutic range. No arbitrary ±20% safe range is generated.
3. **Transparent Calculation Pathways**:
   - **Calculation method: IWPC pharmacogenetic algorithm**: Used when CYP2C9 and VKORC1 genotypes required for the pharmacogenetic pathway are available.
   - **Calculation method: IWPC clinical algorithm**: Used when complete PGx information is not available (or when CPIC requirements for African ancestry are not met). Missing genotypes are **never assumed to be normal**.
4. **CPIC Ancestry-Specific Genetic Rules**:
   - **Non-African Ancestry**:
     - CYP2C9 *5, *6, *8, or *11 detected: 15–30% decrease consideration (20–40% if ≥2 alleles; Strength: Optional).
     - CYP4F2 rs2108622 T carrier (CYP4F2*3): optional 5–10% increase consideration (Strength: Optional).
     - rs12777823 is not used to modify dose in non-African populations.
   - **African Ancestry**:
     - Expanded CYP2C9 alleles (*5, *6, *8, *11) must all be tested. If any are untested/unavailable, CPIC directs clinicians to dose clinically (IWPC clinical algorithm). If tested, *5/*6/*8/*11 considerations apply (Strength: Moderate).
     - For African Americans carrying rs12777823 A (A/G or A/A): 10–25% dose-reduction recommendation (Strength: Moderate). Note: CPIC's recommendation was demonstrated specifically in African Americans (predominantly West African ancestry); its applicability across all African populations is uncertain.
     - CYP4F2 is not used for African ancestry.
   - **Separate Presentation**: CPIC percentage considerations are displayed separately and are **never automatically combined or compounded** into the IWPC point estimate.
5. **Prominent Clinical Notices & Warnings**:
   - **INR Monitoring**: This estimate does not replace INR-guided dose adjustment. Warfarin therapy must be individualized according to INR response and clinical factors.
   - **PGx Data Note**: Results derived from consumer raw DNA files may have incomplete marker coverage and are not equivalent to comprehensive clinical pharmacogenetic testing. Xcode Life does not perform clinical diagnostic genotyping; actionable findings require confirmation with an appropriately validated clinical PGx test before altering therapy.
   - **Alternative Anticoagulant Consideration**: When genotypes associated with CYP2C9 poor metabolism (*2/*3, *3/*3, etc.) or high VKORC1 sensitivity are identified, CPIC advises considering an alternative oral anticoagulant.
6. **FDA Label Genotype Reference Restrictions**:
   - The U.S. FDA Coumadin table contains only 6 diplotypes (*1/*1, *1/*2, *1/*3, *2/*2, *2/*3, *3/*3). It does not include *11, *5, *6, or *8. Expanded alleles are never incorrectly mapped to the *1/*1 label range. The FDA reference is maintained strictly as an external literature reference.

---

## 2. Mathematical Equations

### IWPC Clinical Algorithm
$$\sqrt{\text{weekly dose}} = 4.0376 - 0.2546(\text{age}_{\text{decades}}) + 0.0118(\text{height}_{\text{cm}}) + 0.0134(\text{weight}_{\text{kg}}) - 0.6752(\text{Asian}) + 0.4060(\text{Black/African American}) + 0.0443(\text{Mixed/Unknown}) + 1.2799(\text{inducer}) - 0.5695(\text{amiodarone})$$

$$\text{Weekly dose (mg/week)} = (\sqrt{\text{weekly dose}})^2$$
$$\text{Average daily equivalent (mg/day)} = \frac{\text{Weekly dose}}{7}$$

### IWPC Pharmacogenetic Algorithm (Full Published Model)
$$\sqrt{\text{weekly dose}} = 5.6044 - 0.2614(\text{age}_{\text{decades}}) + 0.0087(\text{height}_{\text{cm}}) + 0.0128(\text{weight}_{\text{kg}}) - 0.8677(\text{VKORC1}_{\text{GA}}) - 1.6974(\text{VKORC1}_{\text{AA}}) - 0.4854(\text{VKORC1}_{\text{unknown}}) - 0.5211(\text{CYP2C9}_{*1/*2}) - 0.9357(\text{CYP2C9}_{*1/*3}) - 1.0616(\text{CYP2C9}_{*2/*2}) - 1.9206(\text{CYP2C9}_{*2/*3}) - 2.3312(\text{CYP2C9}_{*3/*3}) - 0.2188(\text{CYP2C9}_{\text{unknown}}) - 0.1092(\text{Asian}) - 0.2760(\text{Black/African American}) - 0.1032(\text{Mixed/Unknown}) + 1.1816(\text{inducer}) - 0.5503(\text{amiodarone})$$

*Age in decades is binned as $\min(\lfloor\text{age}/10\rfloor, 9)$ (e.g. 70–79 = 7, $\ge 90 = 9$).*
*Note on unknown genotype terms: The published 2009 IWPC equation included coefficients for unknown VKORC1 (−0.4854) and unknown CYP2C9 (−0.2188). Xcode Life does not apply these unknown coefficients; when genotype data are incomplete or unavailable, Xcode Life instead uses the dedicated IWPC clinical dosing algorithm, consistent with CPIC implementation guidance.*

---

## 3. Project Structure

```
Xcode_Warfarin_Calculator/
├── backend/
│   ├── app.py                   # Flask app that serves the calculator locally
│   ├── warfarin_logic.py        # IWPC and CPIC dosing logic
│   └── requirements.txt         # Python dependencies for the app
├── frontend/
│   ├── index.html               # Calculator UI
│   ├── app.js                   # Frontend logic and API requests
│   ├── styles.css               # Page styling
│   └── assets/
│       └── xcode-life-logo.png  # Branding asset
├── README.md                    # Project documentation
├── .gitignore
├── .venv                        # Local virtual environment (created by you)
└── requirements.txt             # Optional root file if needed for other env setups
```

> For local use, you only need the backend and frontend folders. Deployment files are optional and not required for running the app on your machine.

---

## 4. How to Run and Use This Calculator Locally

### Step 1: Create a virtual environment

Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
```

Then activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install the required Python packages

```powershell
pip install -r backend\requirements.txt
```

### Step 3: Start the app

```powershell
python backend\app.py
```

After the server starts, open this in your browser:

```text
http://127.0.0.1:5000
```

### Step 4: Use the calculator

1. Enter the patient age, height, and weight.
2. Choose the appropriate patient ancestry or population category.
3. Select medication factors such as amiodarone use or enzyme inducers.
4. Add genotype data if available, or leave them blank to use the clinical dosing pathway.
5. Click Calculate.
6. Review the result, including the estimated weekly dose and the daily equivalent.

### What the calculator provides

- Estimated stable warfarin maintenance dose in mg/week
- Equivalent average daily dose in mg/day
- Calculation pathway used: clinical or pharmacogenetic
- Clinical/PGx notes and warnings when relevant

### Important notes

- This tool is for estimation only and does not replace clinical judgment.
- It is not a loading-dose calculator and does not replace INR-guided dose adjustment.
- Missing genetic data are not assumed to be normal.
- The calculator is meant to support clinical review, not act as a prescription.

### Optional validation

If you want to confirm the calculation logic before using the app:

```powershell
python -m unittest discover -s backend
```

This checks the local dosing logic and backend behavior.

---

## 5. Scientific References

1. **International Warfarin Pharmacogenetics Consortium (IWPC).** Estimation of the warfarin dose with clinical and pharmacogenetic data. *N Engl J Med.* 2009;360(8):753–764. [DOI: 10.1056/NEJMoa0809329](https://doi.org/10.1056/NEJMoa0809329).
2. **Johnson JA, Caudle KE, Gong L, et al.** Clinical Pharmacogenetics Implementation Consortium (CPIC) Guideline for Pharmacogenetics-Guided Warfarin Dosing: 2017 Update. *Clin Pharmacol Ther.* 2017;102(3):397–404. [PubMed: 28198005](https://pubmed.ncbi.nlm.nih.gov/28198005/).
3. **CPIC Warfarin Guideline Supplementary Material and Evidence Tables (2017).** [CPIC PGx Publication](https://files.cpicpgx.org/data/guideline/publication/warfarin/2017/warfarin.pdf).
4. **U.S. National Library of Medicine / DailyMed.** Warfarin Sodium Tablets Prescribing Information. Expected maintenance-dose ranges by CYP2C9 and VKORC1 genotypes. [DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=bd6ea120-5d1c-4815-94f2-81e28dc6b7a9).
5. **U.S. Food and Drug Administration (FDA).** Direct-to-Consumer Tests: Pharmacogenetic Tests. [FDA DTC PGx](https://www.fda.gov/medical-devices/in-vitro-diagnostics/direct-consumer-tests#pharmacogenetic).
