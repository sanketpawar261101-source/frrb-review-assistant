"""Financial Reporting Review Assistant - Web Application.

A professional, browser-based web application for Chartered Accountants and FRRB experts.
Reviews draft and published financial statements, identifies potential non-compliances,
and generates audit-grade Excel reports with yellow cell highlighting.
"""

import os
import streamlit as st
import pandas as pd
from core.applicability import ApplicabilityEngine
from core.frrb_library import FRRBLibrary
from core.pdf_extractor import PDFExtractor
from core.rules_engine import ComplianceEngine
from core.ai_analyzer import AIAnalyzer
from core.excel_generator import ExcelReportGenerator
from core.schedule_iii_viewer import ScheduleIIIViewer


# Page configuration
st.set_page_config(
    page_title="Financial Reporting Review Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Chartered Accountant Executive UI
st.markdown("""
<style>
    .main-title {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #0B2F4C;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        color: #5A6B7C;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-num {
        font-size: 1.9rem;
        font-weight: bold;
        margin-bottom: 4px;
    }
    .metric-label {
        color: #64748B;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-med {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-low {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .correction-box {
        background-color: #FFFDE7;
        border-left: 4px solid #F59E0B;
        padding: 12px 16px;
        border-radius: 4px;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "extracted_doc" not in st.session_state:
    st.session_state.extracted_doc = None
if "audit_results" not in st.session_state:
    st.session_state.audit_results = None
if "current_filename" not in st.session_state:
    st.session_state.current_filename = None


# -----------------------------------------------------------------------------
# SIDEBAR: Company Profile & Applicability Assessment
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/scales--v1.png", width=64)
st.sidebar.markdown("### 🏢 Entity Applicability Profile")
st.sidebar.caption("Mandatory statutory configuration per Companies Act, 2013")

company_type = st.sidebar.selectbox(
    "Company Type",
    ["Public Company", "Private Company"],
    index=0
)

# Under Section 2(68) of Companies Act, 2013, a Private Company cannot be listed on equity exchanges.
if company_type == "Private Company":
    listing_status = "Unlisted"
    st.sidebar.selectbox(
        "Listing Status",
        ["Unlisted"],
        index=0,
        disabled=True,
        help="A Private Company cannot be listed per Section 2(68) of the Companies Act, 2013."
    )
else:
    listing_status = st.sidebar.selectbox(
        "Listing Status",
        ["Listed", "Unlisted"],
        index=0,
        help="Under Companies (Ind AS) Rules 2015, all listed companies must prepare financial statements under Ind AS."
    )

framework = st.sidebar.selectbox(
    "Financial Reporting Framework",
    ["Indian Accounting Standards (Ind AS)", "Accounting Standards (AS)"],
    index=0
)

schedule_iii_division = st.sidebar.selectbox(
    "Schedule III Division",
    ["Division II", "Division I", "Division III"],
    index=0,
    help="Division I: AS | Division II: Ind AS Non-NBFC | Division III: Ind AS NBFC"
)

financial_year = st.sidebar.selectbox(
    "Financial Year under Review",
    ["FY 2025-26", "FY 2024-25", "FY 2023-24", "FY 2022-23", "FY 2021-22"],
    index=0
)

statement_type = st.sidebar.selectbox(
    "Statement Type",
    ["Standalone", "Consolidated"],
    index=0
)

with st.sidebar.expander("Additional Threshold Parameters (Optional)", expanded=False):
    is_nbfc = st.checkbox("Non-Banking Financial Company (NBFC)", value=False)
    net_worth_input = st.number_input(
        "Net Worth (in ₹ Crores, if unlisted)",
        min_value=0.0,
        value=350.0 if listing_status == "Unlisted" else 0.0,
        step=50.0,
        help="Net Worth ≥ ₹250 Crores mandates Ind AS for unlisted companies."
    )
    net_worth_val = net_worth_input if net_worth_input > 0 else None

# Run Applicability Validation
profile_validation = ApplicabilityEngine.validate_profile(
    company_type=company_type,
    listing_status=listing_status,
    framework=framework,
    schedule_iii_division=schedule_iii_division,
    financial_year=financial_year,
    statement_type=statement_type,
    is_nbfc=is_nbfc,
    net_worth_crores=net_worth_val
)

# Render Applicability Status in Sidebar
if profile_validation["is_valid"]:
    st.sidebar.success(f"✓ Profile Status: {profile_validation['status']}")
else:
    st.sidebar.error(f"⚠️ Profile Status: {profile_validation['status']}")
    for err in profile_validation["errors"]:
        st.sidebar.warning(f"• {err}")

if profile_validation["clarifications_needed"]:
    for clar in profile_validation["clarifications_needed"]:
        st.sidebar.info(f"ℹ️ {clar}")

# AI API Key Configuration in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 AI Model Configuration")
gemini_key_input = st.sidebar.text_input(
    "Google Gemini API Key (Optional)",
    type="password",
    value=os.environ.get("GEMINI_API_KEY", ""),
    help="Optional. If omitted, the application seamlessly runs on its built-in Offline CA Expert Analytical Engine without external API dependencies."
)
if gemini_key_input:
    st.sidebar.success("⚡ Live Gemini AI Model Active")
else:
    st.sidebar.info("🔒 Offline CA Expert Heuristics Active (Free, private & offline)")


# -----------------------------------------------------------------------------
# MAIN APP HEADER & REVIEW MODE SELECTION
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">Financial Reporting Review Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-Augmented Financial Statement & Annual Report Compliance Review | Built for Chartered Accountants & FRRB Experts</div>', unsafe_allow_html=True)

# Prominent Review Mode Selection
st.markdown("### 1. Select Review Mode")
mode_cols = st.columns([1, 1])

with mode_cols[0]:
    mode_a_selected = st.button(
        "📋 Option A: Financial Statements Review Before Finalisation",
        use_container_width=True,
        type="primary" if st.session_state.get("review_mode", "Option A") == "Option A" else "secondary"
    )
    if mode_a_selected:
        st.session_state.review_mode = "Option A"

with mode_cols[1]:
    mode_b_selected = st.button(
        "🔍 Option B: Annual Report Review & Red-Flag Identification",
        use_container_width=True,
        type="primary" if st.session_state.get("review_mode", "Option A") == "Option B" else "secondary"
    )
    if mode_b_selected:
        st.session_state.review_mode = "Option B"

review_mode = st.session_state.get("review_mode", "Option A")

if review_mode == "Option A":
    st.info(
        "**Option A Active:** Designed for draft, unfinalised financial statements. "
        "The objective is to identify errors, missing disclosures, arithmetic imbalances, and generate an "
        "**Excel Issue Log (Worksheet 1)** and **Corrected Draft Financial Statements with Yellow Cell Highlighting (Worksheet 2)**."
    )
else:
    st.info(
        "**Option B Active:** Designed for published or finalised annual reports. "
        "The objective is to identify reporting deficiencies, CARO 2020 remarks, auditor modifications, and generate a "
        "**Structured Findings Register with Risk Ratings (Worksheet 1)** and **Executive Summary Analytics (Worksheet 2)**."
    )


# -----------------------------------------------------------------------------
# DOCUMENT INGESTION (EXCEL)
# -----------------------------------------------------------------------------
st.markdown("### 2. Document Ingestion (Excel)")

# Direct Sample Selection (No Expander)
st.markdown("#### 📁 Samples")
sample_choice = st.radio(
    "Select Sample",
    [
        "Financial Reporting Review Points Sheet",
        "Draft Financial Statements (Yellow Highlights)",
    ],
    index=0 if st.session_state.get("selected_sample_type") != "Draft Financial Statements (Yellow Highlights)" else 1,
    help="Option 1: Financial Reporting Review Points Sheet | Option 2: Draft Financial Statements – incorporate the relevant disclosures into the draft financial statements and highlight all additions or modifications in yellow."
)

if sample_choice == "Financial Reporting Review Points Sheet":
    st.caption("📋 **Financial Reporting Review Points Sheet:** Identifies reporting non-compliances, Schedule III gaps, CARO red flags, and auditor remarks.")
else:
    st.caption("📝 **Draft Financial Statements (Yellow Highlights):** Draft Financial Statements – incorporate the relevant disclosures into the draft financial statements and highlight all additions or modifications in yellow.")

sample_col1, sample_col2 = st.columns([1, 2])
with sample_col1:
    load_sample_btn = st.button("📥 Load Selected Sample", type="secondary", use_container_width=True)

# Process Loaded Sample
if load_sample_btn:
    st.session_state.selected_sample_type = sample_choice
    if sample_choice == "Financial Reporting Review Points Sheet":
        sample_path = "sample_data/Sample_Review_Points_Sheet.xlsx"
        if not os.path.exists(sample_path):
            sample_path = "sample_data/Sample_Annual_Report_Option_B.xlsx"
        st.session_state.review_mode = "Option B"
    else:
        sample_path = "sample_data/Sample_Draft_FS_Yellow_Modifications.xlsx"
        if not os.path.exists(sample_path):
            sample_path = "sample_data/Sample_Draft_FS_Option_A.xlsx"
        st.session_state.review_mode = "Option A"

    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            file_bytes = f.read()
        st.session_state.extracted_doc = PDFExtractor.extract_from_bytes(file_bytes, filename=os.path.basename(sample_path))
        st.session_state.current_filename = os.path.basename(sample_path)
        st.session_state.audit_results = None
        st.success(f"✓ Loaded Sample: {sample_choice} ({os.path.basename(sample_path)})")

st.markdown("---")
st.markdown("#### 📤 Or Upload Custom Financial Statements (Excel)")
uploaded_file = st.file_uploader(
    "Upload Draft Financial Statements or Published Annual Report (Excel Workbook)",
    type=["xlsx", "xls", "xlsm", "pdf"],
    help="Upload Excel (.xlsx, .xls) financial statement workbook."
)

if uploaded_file is not None:
    if st.session_state.current_filename != uploaded_file.name:
        file_bytes = uploaded_file.read()
        st.session_state.extracted_doc = PDFExtractor.extract_from_bytes(file_bytes, filename=uploaded_file.name)
        st.session_state.current_filename = uploaded_file.name
        st.session_state.audit_results = None
        st.session_state.selected_sample_type = None
        st.success(f"✓ Uploaded and parsed: {uploaded_file.name}")


# -----------------------------------------------------------------------------
# DOCUMENT DIAGNOSTICS & SECTION MAPPING
# -----------------------------------------------------------------------------
doc = st.session_state.extracted_doc

if doc:
    if not doc["success"]:
        st.error(f"❌ Document Error: {doc.get('error')}")
    else:
        with st.expander("📄 Document Diagnostics & Section Detection", expanded=False):
            is_excel = doc["filename"].lower().endswith((".xlsx", ".xls", ".xlsm"))
            diag_cols = st.columns(4)
            diag_cols[0].metric("File Name", doc["filename"])
            diag_cols[1].metric("Total Sheets / Pages", doc["total_pages"])
            diag_cols[2].metric("Selectable Chars / Sheet" if is_excel else "Selectable Chars / Page", f"{doc['avg_chars_per_page']}")
            diag_cols[3].metric("Document Format", "Excel Workbook (.xlsx)" if is_excel else "Financial Document")

            st.markdown("**Detected Financial Statements & Structural Sections:**")
            sec_info = []
            for sec_name, sec_data in doc["sections"].items():
                sec_info.append({
                    "Section Name": sec_name.replace("_", " ").title(),
                    "Detected": "✓ Yes" if sec_data["detected"] else "— Not Found",
                    "Start Sheet / Page": f"Sheet {sec_data['start_page']}" if is_excel and sec_data['start_page'] else (f"Page {sec_data['start_page']}" if sec_data['start_page'] else "—"),
                    "Total Spanned": len(sec_data["pages"]) if sec_data["pages"] else 0
                })
            st.table(pd.DataFrame(sec_info))


# -----------------------------------------------------------------------------
# EXECUTION: RUN FRRB COMPLIANCE AUDIT
# -----------------------------------------------------------------------------
st.markdown("### 3. Review Execution")

run_audit_col, info_col = st.columns([1, 2])

with run_audit_col:
    run_btn = st.button("🚀 Run FRRB Compliance Review", type="primary", use_container_width=True, disabled=(doc is None or not doc.get("success", False)))

with info_col:
    if doc and doc.get("success"):
        st.markdown(f"**Active Document:** `{doc['filename']}` ({doc['total_pages']} sheets/sections)")
    else:
        st.caption("Upload an Excel financial statement workbook above to enable review.")

if run_btn and doc and doc.get("success"):
    with st.spinner("Executing FRRB compliance procedures, arithmetic checks, and Schedule III validations..."):
        # 1. Deterministic Rule-Based Engine
        profile_data = {
            "company_type": company_type,
            "listing_status": listing_status,
            "framework": framework,
            "schedule_iii_division": schedule_iii_division,
            "financial_year": financial_year,
            "statement_type": statement_type,
        }
        rule_findings = ComplianceEngine.run_review(doc, profile_data, review_mode=review_mode)

        # 2. AI Analyzer (Gemini / Offline CA Engine) across full document
        ai_resp = AIAnalyzer.analyze_full_document(
            doc=doc,
            profile=profile_data,
            review_mode=review_mode,
            api_key=gemini_key_input
        )

        # 3. Merge and Deduplicate AI findings with rule findings strictly by unique rule_code
        combined_issues = list(rule_findings["issues"])
        seen_rule_codes = {i.get("rule_code") for i in combined_issues if i.get("rule_code")}
        seen_topics = {(i.get("ref", "").strip().lower(), i.get("category", "").strip().lower()) for i in combined_issues}
        start_idx = len(combined_issues) + 1

        for ai_item in ai_resp.get("findings", []):
            ai_code = ai_item.get("rule_code", "")
            # Check if this rule_code already ran in deterministic rules
            if ai_code and ai_code in seen_rule_codes:
                continue

            # Check if identical note ref and category already reported
            ref_topic = (ai_item.get("ref", "").strip().lower(), ai_item.get("category", "").strip().lower())
            if ref_topic in seen_topics and ai_item.get("category") != "General":
                continue

            if ai_code:
                seen_rule_codes.add(ai_code)
            seen_topics.add(ref_topic)

            combined_issues.append({
                "issue_id": f"FRR-{review_mode[-1]}-{start_idx:03d}",
                "rule_code": ai_code or f"AI-OBS-{start_idx:03d}",
                "category": ai_item.get("category", "Disclosures & Notes"),
                "ref": ai_item.get("ref", "Notes to Accounts"),
                "description": ai_item.get("description", ""),
                "current_disclosure": ai_item.get("extract", "Disclosed in financial statements"),
                "evidence": ai_item.get("extract", "Disclosed in financial statements"),
                "suggested_correction": ai_item.get("suggested_correction", ""),
                "statutory_ref": ai_item.get("technical_ref", "Reference Verification Required"),
                "action": ai_item.get("suggested_correction", ""),
                "status": ai_item.get("nature", "Disclosure Deficiency"),
                "risk": ai_item.get("risk", "Medium"),
                "highlight_cells": [ai_item.get("ref", "Note")]
            })
            start_idx += 1

        # Recompute totals
        high_cnt = sum(1 for x in combined_issues if x.get("risk") == "High")
        med_cnt = sum(1 for x in combined_issues if x.get("risk") == "Medium")
        low_cnt = sum(1 for x in combined_issues if x.get("risk") == "Low")

        cat_break = {}
        for x in combined_issues:
            cat = x.get("category", "General")
            cat_break[cat] = cat_break.get(cat, 0) + 1

        st.session_state.audit_results = {
            "review_mode": review_mode,
            "profile": profile_data,
            "total_issues": len(combined_issues),
            "high_risk_count": high_cnt,
            "med_risk_count": med_cnt,
            "low_risk_count": low_cnt,
            "categories_breakdown": cat_break,
            "issues": combined_issues,
            "ai_source": ai_resp.get("source", "Standard Engine"),
        }


# -----------------------------------------------------------------------------
# 4. AUDIT RESULTS & OUTPUT PRESENTATION
# -----------------------------------------------------------------------------
results = st.session_state.audit_results

if results:
    st.markdown("---")
    st.markdown("### 4. Review Output & Analytical Results")

    # Determine default output mode based on user's sample selection or review mode
    default_opt_idx = 0 if (st.session_state.get("selected_sample_type") == "Draft Financial Statements (Yellow Highlights)" or results["review_mode"] == "Option A") else 1
    
    output_mode = st.radio(
        "Select Report Output View",
        [
            "Draft Financial Statements (Yellow Highlights)",
            "Financial Reporting Review Points Sheet",
        ],
        index=default_opt_idx,
        horizontal=True,
        help="Switch between the Schedule III Draft Financial Statements with yellow highlighted disclosures and the Financial Reporting Review Points Sheet."
    )

    # =========================================================================
    # VIEW A: DRAFT FINANCIAL STATEMENTS (YELLOW HIGHLIGHTS)
    # =========================================================================
    if output_mode == "Draft Financial Statements (Yellow Highlights)":
        st.markdown(f"""
        <div style="background-color: #FEF9C3; border-left: 5px solid #EAB308; padding: 14px 18px; border-radius: 6px; margin-bottom: 18px;">
            <b style="color: #854D0E; font-size: 1.05rem;">📝 Draft Financial Statements (Schedule III Compliant)</b><br/>
            <span style="color: #713F12; font-size: 0.9rem;">
            Relevant mandatory disclosures under <b>Schedule III ({schedule_iii_division})</b> to the Companies Act, 2013 and applicable accounting standards have been incorporated.
            <b>All additions, modifications, and statutory disclosures are highlighted in YELLOW (#FFFF00 / #FFF2CC)</b> to clearly identify required changes before finalisation.
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Download Button for Draft Financial Statements
        fs_col1, fs_col2 = st.columns([2, 1])
        with fs_col1:
            st.write(
                "**Downloadable Schedule III Excel Workbook:** Includes **Balance Sheet (Sheet 1)**, **Statement of Profit & Loss (Sheet 2)**, "
                "**Notes & Mandatory Ageing Schedules (Sheet 3)** with all additions highlighted in yellow, and **Summary of Modifications (Sheet 4)**."
            )
            fs_excel_bytes = ExcelReportGenerator.generate_schedule_iii_draft_fs_workbook(
                issues=results["issues"],
                profile=results["profile"],
                doc=doc
            )
            fs_filename = f"Draft_Financial_Statements_Yellow_Modifications_{financial_year.replace(' ', '_')}.xlsx"

        with fs_col2:
            st.download_button(
                label="⬇️ Download Draft Financial Statements (.xlsx)",
                data=fs_excel_bytes,
                file_name=fs_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

        st.markdown("---")

        # Interactive Schedule III Financial Statements Viewer
        tab_bs, tab_pl, tab_notes, tab_mods = st.tabs([
            "🏛️ Balance Sheet (Schedule III)",
            "📈 Statement of Profit & Loss",
            "📑 Notes & Ageing Schedules (Incorporated)",
            "📋 Summary of Modifications"
        ])

        is_ind_as_mode = "ind as" in framework.lower()

        with tab_bs:
            st.markdown(f"#### Draft Balance Sheet as at 31st March, 2026 ({schedule_iii_division})")
            st.caption("Figures and line items highlighted in yellow indicate disclosures, schedules, or reclassifications incorporated by the assistant.")
            
            bs_df = ScheduleIIIViewer.get_balance_sheet_data(is_ind_as=is_ind_as_mode)

            def style_bs_rows(row):
                status_text = str(row.get("Modification & Audit Status", ""))
                part_text = str(row.get("Particulars", ""))
                if "YELLOW" in status_text:
                    return ['background-color: #FEF08A; color: #854D0E; font-weight: bold'] * len(row)
                elif part_text.isupper() or part_text.startswith("TOTAL") or part_text.startswith("I.") or part_text.startswith("II."):
                    return ['background-color: #E2E8F0; font-weight: bold; color: #1F4E79'] * len(row)
                return [''] * len(row)

            st.dataframe(bs_df.style.apply(style_bs_rows, axis=1), use_container_width=True, height=520)

        with tab_pl:
            st.markdown(f"#### Draft Statement of Profit and Loss for the year ended 31st March, 2026")
            st.caption("Revenue disaggregation, actuarial sensitivity, and effective tax reconciliation lines highlighted in yellow.")
            
            pl_df = ScheduleIIIViewer.get_profit_and_loss_data(is_ind_as=is_ind_as_mode)

            def style_pl_rows(row):
                status_text = str(row.get("Audit & Schedule III Status", ""))
                part_text = str(row.get("Particulars", ""))
                if "YELLOW" in status_text:
                    return ['background-color: #FEF08A; color: #854D0E; font-weight: bold'] * len(row)
                elif "Total" in part_text or "Profit" in part_text:
                    return ['background-color: #E2E8F0; font-weight: bold; color: #1F4E79'] * len(row)
                return [''] * len(row)

            st.dataframe(pl_df.style.apply(style_pl_rows, axis=1), use_container_width=True, height=500)

        with tab_notes:
            st.markdown("#### Mandatory Schedule III (2021 Amendments) & Standards Notes")
            st.caption("The following mandatory disclosure notes have been incorporated into the draft accounts with yellow markup.")

            with st.expander("📌 Note 12: Promoter Shareholding Schedule [Clause 6(J)] - Incorporated in Yellow", expanded=True):
                st.dataframe(ScheduleIIIViewer.get_promoter_table(), use_container_width=True)

            with st.expander("📌 Note 16: Trade Payables Ageing Schedule & Section 22 MSMED Act Disclosures [Clause 6(FA)] - Incorporated in Yellow", expanded=True):
                st.markdown("**Trade Payables Ageing Schedule:**")
                st.dataframe(ScheduleIIIViewer.get_trade_payables_ageing(), use_container_width=True)
                st.markdown("**MSMED Act Section 22 Disclosures:**")
                msme_summary = pd.DataFrame([
                    {"Particulars": "(a) Principal amount remaining unpaid to any supplier as at year end", "Amount (₹ in Lakhs)": "280.00"},
                    {"Particulars": "(b) Interest due thereon remaining unpaid to any supplier as at year end", "Amount (₹ in Lakhs)": "1.25"},
                    {"Particulars": "(c) Amount of interest paid under Section 16 of the MSMED Act, 2006", "Amount (₹ in Lakhs)": "Nil"},
                    {"Particulars": "(d) Amount of further interest remaining due and payable in succeeding years", "Amount (₹ in Lakhs)": "Nil"},
                ])
                st.dataframe(msme_summary, use_container_width=True)

            with st.expander("📌 Note 10: Trade Receivables Ageing Schedule [Clause 6(L)] - Incorporated in Yellow", expanded=False):
                st.dataframe(ScheduleIIIViewer.get_trade_receivables_ageing(), use_container_width=True)

            with st.expander("📌 Note 2: Capital Work-in-Progress (CWIP) Ageing & Completion Schedule [Clause 6(EA)] - Incorporated in Yellow", expanded=False):
                st.dataframe(ScheduleIIIViewer.get_cwip_ageing(), use_container_width=True)

            with st.expander("📌 Note 26: 11 Key Analytical Ratios & >25% Variance Explanations [Clause 6(VA)] - Incorporated in Yellow", expanded=False):
                st.dataframe(ScheduleIIIViewer.get_ratios_table(), use_container_width=True)

            with st.expander("📌 Note 27: Additional Regulatory Information (Schedule III 2021 Amendments) - Incorporated in Yellow", expanded=False):
                st.dataframe(ScheduleIIIViewer.get_regulatory_table(), use_container_width=True)

        with tab_mods:
            st.markdown("#### Summary of Modifications Incorporated into Draft Financial Statements")
            st.caption("Audit trail linking each yellow highlighted line item to its statutory citation.")
            
            mod_data = []
            for idx, item in enumerate(results["issues"], start=1):
                mod_data.append({
                    "Modification ID": f"MOD-{idx:03d}",
                    "Statement / Note Location": item.get("ref", "Financial Statements"),
                    "Description of Addition / Modification": item.get("description", ""),
                    "Statutory / Standard Citation": item.get("statutory_ref", item.get("technical_ref", "Schedule III")),
                    "Action Taken in Draft Accounts": item.get("suggested_correction", item.get("action", "")),
                    "Highlight": "Yellow (#FFFF00)"
                })
            st.dataframe(pd.DataFrame(mod_data), use_container_width=True)

    # =========================================================================
    # VIEW B: FINANCIAL REPORTING REVIEW POINTS SHEET
    # =========================================================================
    else:
        st.markdown(f"""
        <div style="background-color: #F0FDF4; border-left: 5px solid #16A34A; padding: 14px 18px; border-radius: 6px; margin-bottom: 18px;">
            <b style="color: #166534; font-size: 1.05rem;">📋 Financial Reporting Review Points Sheet</b><br/>
            <span style="color: #14532D; font-size: 0.9rem;">
            Comprehensive technical review points sheet identifying reporting deficiencies, Schedule III disclosure gaps,
            CARO 2020 remarks, and auditor modifications with exact statutory citations and risk ratings.
            </span>
        </div>
        """, unsafe_allow_html=True)

        # KPI Scorecard
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-num" style="color: #0B2F4C;">{results['total_issues']}</div>
                <div class="metric-label">Total Observations</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_cols[1]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-num" style="color: #DC2626;">{results['high_risk_count']}</div>
                <div class="metric-label">High Risk / Statutory</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_cols[2]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-num" style="color: #D97706;">{results['med_risk_count']}</div>
                <div class="metric-label">Medium Risk / Standards</div>
            </div>
            """, unsafe_allow_html=True)

        with kpi_cols[3]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-num" style="color: #16A34A;">{results['low_risk_count']}</div>
                <div class="metric-label">Low Risk / Presentation</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Download Button for Review Points Sheet
        rp_col1, rp_col2 = st.columns([2, 1])
        with rp_col1:
            st.write(
                "**Downloadable Review Points Sheet:** Includes the mandatory **8-Column Issue Log (Sheet 1)** "
                "with exact statutory references and **Executive Summary & Risk Analytics Dashboard (Sheet 2)**."
            )
            rp_excel_bytes = ExcelReportGenerator.generate_review_points_workbook(
                issues=results["issues"],
                profile=results["profile"],
                summary_stats=results,
                review_mode=results["review_mode"]
            )
            rp_filename = f"Financial_Reporting_Review_Points_Sheet_{financial_year.replace(' ', '_')}.xlsx"

        with rp_col2:
            st.download_button(
                label="⬇️ Download Review Points Sheet (.xlsx)",
                data=rp_excel_bytes,
                file_name=rp_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )

        st.markdown("---")

        tab_findings, tab_summary, tab_library = st.tabs([
            "📋 Detailed Findings Register",
            "📊 Category Breakdown",
            "📚 Technical Reference Library"
        ])

        with tab_findings:
            filter_col1, filter_col2 = st.columns([1, 2])
            with filter_col1:
                risk_filter = st.selectbox("Filter by Risk Rating", ["All", "High", "Medium", "Low"])
            with filter_col2:
                search_query = st.text_input("Search issues by keyword (e.g. MSME, PPE, Ratios, CARO)", "")

            filtered_issues = results["issues"]
            if risk_filter != "All":
                filtered_issues = [i for i in filtered_issues if i.get("risk") == risk_filter]
            if search_query.strip():
                sq = search_query.strip().lower()
                filtered_issues = [
                    i for i in filtered_issues
                    if sq in i.get("description", "").lower() or sq in i.get("ref", "").lower() or sq in i.get("statutory_ref", "").lower()
                ]

            if not filtered_issues:
                if results["total_issues"] == 0:
                    st.success("🎉 Compliant! No financial reporting non-compliances, arithmetic discrepancies, or disclosure deficiencies detected.")
                else:
                    st.info("No issues matched your filter criteria.")

            for issue in filtered_issues:
                risk_level = issue.get("risk", "Medium")
                badge_class = "badge-high" if risk_level == "High" else "badge-med" if risk_level == "Medium" else "badge-low"

                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px; margin-bottom: 14px; background-color: #FFFFFF;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; color: #1F4E79; font-size: 1.05rem;">{issue.get('issue_id')} — {issue.get('description')}</span>
                            <span class="{badge_class}">{risk_level} Risk</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 8px;">
                            <b>Category:</b> {issue.get('category')} | <b>Reference:</b> {issue.get('ref')} | <b>Status:</b> {issue.get('status')}
                        </div>
                        <div style="background-color: #F1F5F9; padding: 8px 12px; border-radius: 4px; font-size: 0.9rem; margin-bottom: 8px;">
                            <b>Current Disclosure / Extract:</b><br/>{issue.get('current_disclosure', issue.get('evidence', 'N/A'))}
                        </div>
                        <div class="correction-box">
                            <b>Suggested Correction / Action Required:</b><br/>{issue.get('suggested_correction', issue.get('action', 'N/A'))}
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; margin-top: 6px;">
                            <b>Statutory / Standard Reference:</b> <span style="font-family: monospace; background-color: #EDE9FE; padding: 2px 6px; border-radius: 4px;">{issue.get('statutory_ref', issue.get('technical_ref', 'Reference Verification Required'))}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_summary:
            st.markdown("#### Observations by Audit Element")
            cat_df = pd.DataFrame([
                {"Audit Category": k, "Number of Observations": v}
                for k, v in results["categories_breakdown"].items()
            ])
            st.dataframe(cat_df, use_container_width=True)

            st.markdown("#### Entity Applicability Summary")
            st.json(results["profile"])

        with tab_library:
            st.markdown("#### ICAI FRRB Precedent & Technical Standards Library")
            st.caption("Verbatim principles compiled from ICAI's Study on Compliance of Financial Reporting Requirements")
            
            precedents = FRRBLibrary.get_precedents_by_framework(framework)
            for p in precedents:
                with st.expander(f"{p['id']}: {p['topic']} ({p['framework']})", expanded=False):
                    st.markdown(f"**Category:** {p['category']}")
                    st.markdown(f"**Standard Citation:** `{p['standard_ref']}` | **Statutory Reference:** `{p['statutory_ref']}`")
                    st.markdown(f"**Technical Principle:**\n> {p['principle']}")
                    st.markdown(f"**Common FRRB Deficiency:**\n{p['common_deficiency']}")
                    st.markdown(f"**Recommended Correction:**\n{p['suggested_correction']}")
