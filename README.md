# Financial Reporting Review Assistant (FRRB Expert Edition)

A browser-based, AI-augmented analytical application designed for **Chartered Accountants** and **Financial Reporting Review Board (FRRB)** technical reviewers. The application automates the rigorous technical audit of draft financial statements and published annual reports against **Indian Accounting Standards (Ind AS)**, **Accounting Standards (AS)**, **Schedule III** (Divisions I, II, and III), the **Companies Act, 2013**, **CARO 2020**, and authentic **ICAI FRRB** review publications.

---

## 🌟 Key Capabilities

1. **Entity Applicability Assessment & Statutory Guardrails**:
   - Validates entity profile against the *Companies (Indian Accounting Standards) Rules, 2015* and *Schedule III*.
   - Prevents misclassification (e.g., flags Listed companies attempting to apply AS Division I; checks NBFC classification for Division III; prompts for Net Worth threshold verification when unlisted).

2. **Dual-Mode Review Architecture**:
   - **Option A: Financial Statements Review Before Finalisation**
     - Target: Draft accounts and unfinalised notes.
     - Detects arithmetic imbalances ($Assets \neq Equity + Liabilities$), unlinked cash flow figures, missing mandatory disclosures, and standard violations.
     - Generates an **audit-grade Excel Workbook** with an **8-Column Issue Log (Sheet 1)** and a **Complete Financial Model with YELLOW CELL HIGHLIGHTING (Sheet 2)** identifying exact cells requiring correction or addition.
   - **Option B: Annual Report Review and Red-Flag Identification**
     - Target: Published annual reports.
     - Scans Independent Auditor's Reports (Qualified, Adverse, Disclaimer opinions; Emphasis of Matter), CARO 2020 clauses (e.g. Clause 3(ii)(b) quarterly bank statement discrepancies), and accounting policy gaps.
     - Generates a **Structured Red-Flag Register with High/Medium/Low Risk Ratings** and actionable FRRB follow-up procedures.

3. **Traceable Technical References (No Hallucinations)**:
   - Incorporates verbatim principles and citations from the ICAI publication *Study on Compliance of Financial Reporting Requirements (Ind AS Framework)*, amended Schedule III, and CARO 2020.
   - If a standard paragraph cannot be verified with certainty, the system marks it as `"Reference Verification Required"`.

4. **Negative Test Verification (Zero False Positives)**:
   - Built-in validation ensures that compliant statements containing all required disclosures and reconciled balances are not falsely flagged.

5. **AI + Offline Expert Engine**:
   - Optional live **Google Gemini API** integration (`gemini-1.5-flash`) for nuanced NLP disclosure analysis.
   - Intelligent **Offline CA Expert Heuristics Engine** active when no API key is set—enabling 100% offline, private, zero-cost operation.

---

## 📁 Project Architecture

```
Group Project/
├── app.py                      # Main Streamlit web application
├── core/
│   ├── applicability.py        # Framework & Schedule III applicability validator
│   ├── pdf_extractor.py        # PyMuPDF parser, section locator & scanned doc detector
│   ├── rules_engine.py         # Deterministic compliance & arithmetic audit engine
│   ├── frrb_library.py         # Curated ICAI FRRB precedents and technical references
│   ├── ai_analyzer.py          # AI disclosure analysis (Gemini API + offline expert heuristics)
│   └── excel_generator.py      # Professional Excel generator with yellow cell highlighting
├── sample_data/
│   ├── generate_sample_pdfs.py # Generator for reproducible test cases
│   ├── Sample_Draft_FS_Option_A_With_Errors.pdf
│   ├── Sample_Annual_Report_Option_B_RedFlags.pdf
│   └── Sample_Compliant_FS_Negative_Test.pdf
├── tests/
│   ├── test_applicability.py   # Unit tests for applicability rules
│   ├── test_pdf_extractor.py   # Unit tests for PDF parsing and scanned doc detection
│   ├── test_rules_engine.py    # Integration tests for Option A, Option B & Negative test
│   └── test_excel_generator.py # Tests for Excel 8 columns & yellow highlighting
├── requirements.txt            # Python dependencies
└── README.md                   # System documentation and demonstration guide
```

---

## 🚀 Installation & Application Startup

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Operating System: Windows, macOS, or Linux

### 2. Install Dependencies
Open PowerShell or your command prompt in the project root directory and run:

```powershell
pip install -r requirements.txt
```

### 3. Launch the Web Application
Run the following command:

```powershell
streamlit run app.py
```

Streamlit will launch local server and automatically open the application in your default web browser at:
`http://localhost:8501`

---

## ⚙️ Configuration & AI Setup

### Optional Gemini API Key Setup
The application is designed to be fully operational out-of-the-box without requiring an external API key. However, to enable live Google Gemini analysis:
- **Option 1 (Interactive UI)**: Enter your key in the sidebar under `🤖 AI Model Configuration`. It remains strictly in your session state and is never saved to disk.
- **Option 2 (Environment Variable)**: Set `GEMINI_API_KEY` before launching:
  ```powershell
  $env:GEMINI_API_KEY="your-gemini-api-key-here"
  streamlit run app.py
  ```

---

## ⏱️ 10–15 Minute Demonstration Guide

Follow these sequential steps to demonstrate the application to fellow Chartered Accountants, partners, or review committees:

### Step 1: Demonstrate Entity Applicability Assessment (2 Minutes)
1. In the sidebar under **Entity Applicability Profile**, select:
   - `Company Type`: **Public Company**
   - `Listing Status`: **Listed**
   - `Financial Reporting Framework`: Select **Accounting Standards (AS)**
   - `Schedule III Division`: Select **Division I**
2. Notice the real-time **Statutory Violation Alert**:
   > *“Statutory Violation: Under Rule 4(1)(iii)(a) of Companies (Ind AS) Rules, 2015, any company whose equity or debt securities are listed MUST prepare financial statements under Ind AS framework.”*
3. Now correct the selection:
   - `Framework`: **Indian Accounting Standards (Ind AS)**
   - `Schedule III Division`: **Division II**
4. Observe the green confirmation badge: `✓ Profile Status: Compliant & Valid`.

---

### Step 2: Demonstrate Review Mode Option A — Draft Financial Statements (4 Minutes)
1. Click **Option A: Financial Statements Review Before Finalisation**.
2. Under **Or Load Demonstration Samples**, select:
   - `Sample 1: Draft FS with Errors (Option A Demo)`
   - Click **Load Selected Sample PDF**.
3. Expand **📄 Document Diagnostics & Section Detection**:
   - Verify page count (3 pages) and automatic identification of *Balance Sheet*, *Profit & Loss*, and *Notes to Accounts*.
4. Click **🚀 Run FRRB Compliance Review**:
   - Review the **KPI Cards**: Highlights Total Observations, High Risk, Medium Risk, and Low Risk items.
   - Inspect the detected findings:
     - **Arithmetic Integrity Check**: Detects that Total Assets (₹11,060 Lakhs) does not match Total Equity & Liabilities (₹10,810 Lakhs).
     - **Cash Flow Reconciliation**: Flags closing cash discrepancy between CFS and Note 9.
     - **Ind AS 16 PPE Policy**: Catches legacy *"standard of performance"* wording and cites Ind AS 16.7/16.13.
     - **Schedule III Trade Payables Ageing**: Flags missing MCA mandatory ageing schedule and Section 22 MSMED Act disclosures.
     - **Schedule III Mandatory Ratios**: Flags ratio variances >25% without required explanatory footnotes.
5. Click **⬇️ Download Pre_Finalisation_Issue_Log_FY_2023-24.xlsx**:
   - Open in Excel:
     - **Worksheet 1 (Issue Log)**: Displays the mandatory 8 columns (`Issue ID`, `Financial statement or note reference`, `Description of the issue`, `Current reference or existing disclosure`, `Correct reference or suggested correction`, `Applicable accounting standard, Schedule III requirement or statutory provision`, `Recommended action`, `Status of the issue`).
     - **Worksheet 2 (Financial Statements Marked)**: Shows draft financial statement line items with **YELLOW HIGHLIGHTED CELLS** pointing out items requiring modifications before finalisation.

---

### Step 3: Demonstrate Review Mode Option B — Annual Report Red Flags (4 Minutes)
1. Click **Option B: Annual Report Review & Red-Flag Identification**.
2. Under **Load Demonstration Samples**, select:
   - `Sample 2: Published Annual Report with Red Flags (Option B Demo)`
   - Click **Load Selected Sample PDF**.
3. Click **🚀 Run FRRB Compliance Review**:
   - Inspect findings:
     - **Auditor's Report Review**: Detects *“Basis for Qualified Opinion”* on unverified inventory under SA 705 / Section 143(2).
     - **CARO 2020 Clause 3(ii)(b)**: Flags reported discrepancies between quarterly statements submitted to banks and financial books.
     - **Auditor's Emphasis of Matter**: Flags unprovisioned GST tax litigation.
     - **Ind AS 109 / Related Parties**: Identifies corporate guarantee given without fair value recognition.
4. Click **⬇️ Download FRRB_Annual_Report_RedFlag_Register_FY_2023-24.xlsx**:
   - Open in Excel:
     - **Worksheet 1 (Red-Flag & Findings Register)**: Structured table with risk color coding (High: Soft Red, Medium: Soft Orange, Low: Soft Green).
     - **Worksheet 2 (Executive Summary & Analytics)**: Scorecard breakdown by risk rating and statutory category.

---

### Step 4: Demonstrate Negative Testing (Zero False Positives) (2 Minutes)
1. Switch to `Sample 3: Clean Compliant FS (Negative Test - Zero False Positives)`.
2. Click **Load Selected Sample PDF** and click **Run FRRB Compliance Review**.
3. Verify that the application displays:
   > *“🎉 Compliant! No financial reporting non-compliances, arithmetic discrepancies, or disclosure deficiencies detected.”*
4. Confirms that compliant disclosures are not falsely flagged.

---

### Step 5: Explore the Technical Reference Library (1 Minute)
1. Navigate to the **📚 Technical Reference Library** tab in the main interface.
2. Search and review authentic ICAI FRRB precedents compiled from the official ICAI publication:
   - Ind AS 16 subsequent cost principles
   - Schedule III Trade Payables MSME ageing rules
   - Schedule III Ratio variance explanation rules
   - CARO 2020 Clause 3(ii)(b) quarterly bank returns reconciliation rules.

---

## 🧪 Running Automated Unit & Integration Tests

To run the complete test suite:

```powershell
python -m unittest discover tests
```

Expected output:
```
Ran 13 tests in 0.25s
OK
```

All 13 automated tests verify:
- Statutory applicability logic (Listed vs Unlisted, AS vs Ind AS, NBFC rules)
- Text-based vs scanned PDF detection
- Arithmetic discrepancy detection
- Schedule III compliance checks
- Both review modes (Option A vs Option B)
- Excel 8-column structure and yellow cell highlighting
- Negative test cases ensuring zero false positives on compliant financial statements.
