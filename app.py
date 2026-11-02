"""Financial Reporting Review Assistant - Web Application.

A professional, browser-based web application for Chartered Accountants and FRRB experts.
Reviews draft and published financial statements, identifies potential non-compliances,
and generates audit-grade Excel reports with yellow cell highlighting.
"""

import html
import os
import streamlit as st
import pandas as pd
from core.applicability import ApplicabilityEngine
from core.frrb_library import FRRBLibrary
from core.pdf_extractor import PDFExtractor
from core.rules_engine import ComplianceEngine
from core.ai_analyzer import AIAnalyzer
from core.excel_generator import ExcelReportGenerator
from core.knowledge_base import KnowledgeBase
from core.fs_marker import DraftFSMarker


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

st.markdown("#### 📁 Output Required")
output_choice = st.radio(
    "Select Output",
    [
        "Financial Reporting Review Points Sheet",
        "Draft Financial Statements (Yellow Highlights)",
    ],
    index=0 if st.session_state.get("output_choice") != "Draft Financial Statements (Yellow Highlights)" else 1,
    help="Option 1: Financial Reporting Review Points Sheet | Option 2: Draft Financial Statements – incorporate the relevant disclosures into the draft financial statements and highlight all additions or modifications in yellow."
)
st.session_state.output_choice = output_choice

if output_choice == "Financial Reporting Review Points Sheet":
    st.caption("📋 **Financial Reporting Review Points Sheet:** Identifies reporting non-compliances, Schedule III gaps, CARO red flags, and auditor remarks.")
else:
    st.caption("📝 **Draft Financial Statements (Yellow Highlights):** Your own draft financial statements are returned in the same format – relevant disclosures are incorporated and every addition or modification is highlighted in yellow.")

st.markdown("---")
st.markdown("#### 📤 Upload Financial Statements (Excel)")
uploaded_file = st.file_uploader(
    "Upload Draft Financial Statements or Published Annual Report (Excel Workbook)",
    type=["xlsx", "xls", "xlsm", "pdf"],
    help="Upload Excel (.xlsx, .xls) financial statement workbook."
)

if uploaded_file is not None:
    if st.session_state.current_filename != uploaded_file.name:
        file_bytes = uploaded_file.read()
        st.session_state.extracted_doc = PDFExtractor.extract_from_bytes(file_bytes, filename=uploaded_file.name)
        st.session_state.source_bytes = file_bytes
        st.session_state.current_filename = uploaded_file.name
        st.session_state.audit_results = None
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

        # Ground every finding in the knowledge base (verified citation + source requirement text)
        combined_issues = [KnowledgeBase.enrich_issue(x, profile_data) for x in combined_issues]

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

    # Default output view follows the user's "Output Required" selection
    default_opt_idx = 0 if st.session_state.get("output_choice") == "Draft Financial Statements (Yellow Highlights)" else 1

    output_mode = st.radio(
        "Select Report Output View",
        [
            "Draft Financial Statements (Yellow Highlights)",
            "Financial Reporting Review Points Sheet",
        ],
        index=default_opt_idx,
        horizontal=True,
        help="Switch between your draft financial statements with yellow highlighted disclosures and the Financial Reporting Review Points Sheet."
    )

    # =========================================================================
    # VIEW A: DRAFT FINANCIAL STATEMENTS (YELLOW HIGHLIGHTS) - ENTITY'S OWN FORMAT
    # =========================================================================
    if output_mode == "Draft Financial Statements (Yellow Highlights)":
        st.markdown(f"""
        <div style="background-color: #FEF9C3; border-left: 5px solid #EAB308; padding: 14px 18px; border-radius: 6px; margin-bottom: 18px;">
            <b style="color: #854D0E; font-size: 1.05rem;">📝 Draft Financial Statements – your format retained</b><br/>
            <span style="color: #713F12; font-size: 0.9rem;">
            The uploaded workbook is returned in exactly the same format (sheets, layout, fonts, number formats and formulas).
            Line items affected by a review point are <b>highlighted in yellow</b> with a cell comment giving the issue ID and reference,
            and the required disclosures under <b>Schedule III ({schedule_iii_division})</b> and the applicable standards are inserted into the
            existing Notes in yellow. Amounts not available in the draft are left as <b>[___]</b> for management to complete.
            </span>
        </div>
        """, unsafe_allow_html=True)

        source_bytes = st.session_state.get("source_bytes")
        current_name = st.session_state.get("current_filename") or ""
        if not source_bytes or not DraftFSMarker.is_supported(current_name):
            st.warning("Draft Financial Statements output needs the draft statements uploaded as an Excel workbook (.xlsx / .xlsm) so that its format can be retained. Please upload the Excel draft, or use the Review Points Sheet view.")
        else:
            marked_bytes, fs_changes = DraftFSMarker.mark(source_bytes, current_name, results["issues"])
            base_name = os.path.splitext(current_name)[0]
            ext = os.path.splitext(current_name)[1].lower()

            fs_col1, fs_col2 = st.columns([2, 1])
            with fs_col1:
                inserted = sum(1 for c in fs_changes if c["type"] == "Disclosure inserted")
                highlighted = sum(1 for c in fs_changes if c["type"] == "Existing line highlighted")
                st.write(f"**{highlighted}** existing line items highlighted and **{inserted}** disclosure lines incorporated. "
                         "A 'Yellow Changes Index' sheet is added at the end of the workbook as the audit trail.")
            with fs_col2:
                st.download_button(
                    label="⬇️ Download Draft Financial Statements",
                    data=marked_bytes,
                    file_name=f"{base_name}_Reviewed_Yellow{ext}",
                    mime="application/vnd.ms-excel.sheet.macroEnabled.12" if ext == ".xlsm" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )

            st.markdown("---")
            preview = DraftFSMarker.preview(marked_bytes, source_bytes)
            sheet_tabs = st.tabs([f"📄 {name}" for name in preview] + ["📋 Yellow Changes Index"])

            for tab, (sheet_name, data) in zip(sheet_tabs, preview.items()):
                with tab:
                    grid, yellow = data["grid"], data["yellow"]
                    if not grid:
                        st.caption("Empty sheet")
                        continue
                    width = max(len(r) for r in grid)
                    grid = [list(r) + [""] * (width - len(r)) for r in grid]
                    yellow = [list(r) + [False] * (width - len(r)) for r in yellow]
                    sheet_df = pd.DataFrame(grid, columns=[chr(65 + i) if i < 26 else f"C{i+1}" for i in range(width)])
                    sheet_df.index = range(1, len(sheet_df) + 1)
                    sheet_df = sheet_df.astype(str).replace({"None": ""})
                    styles = pd.DataFrame(
                        [["background-color: #FFFF00; color: #000000; font-weight: 600" if f else "" for f in r] for r in yellow],
                        index=sheet_df.index, columns=sheet_df.columns
                    )
                    st.dataframe(sheet_df.style.apply(lambda _: styles, axis=None), use_container_width=True, height=min(640, 38 + 35 * len(sheet_df)))

            with sheet_tabs[-1]:
                st.caption("Every yellow change, linked to its review point and reference.")
                st.dataframe(pd.DataFrame(fs_changes), use_container_width=True)

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

                req_html = "".join(
                    f"<div style='margin-top:4px;'><b>{html.escape(p['ref'])}:</b> {html.escape(p['text'][:600])}{'…' if len(p['text']) > 600 else ''}</div>"
                    for p in issue.get("source_requirements", [])
                )
                req_block = (
                    f"<div style='background-color:#EEF2FF; color:#1E1B4B; padding:8px 12px; border-radius:4px; font-size:0.85rem; margin-top:8px;'>"
                    f"<b>Requirement as per the Standard (source text):</b>{req_html}</div>"
                ) if req_html else ""

                with st.container():
                    st.markdown(f"""
                    <div style="border: 1px solid #CBD5E1; border-radius: 8px; padding: 16px; margin-bottom: 14px; background-color: #FFFFFF; color: #0F172A;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 12px;">
                            <span style="font-weight: 700; color: #1F4E79; font-size: 1.05rem;">{issue.get('issue_id')} — {html.escape(issue.get('description', ''))}</span>
                            <span class="{badge_class}">{risk_level} Risk</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #475569; margin-bottom: 8px;">
                            <b>Area:</b> {html.escape(issue.get('category', ''))} | <b>FS / Note reference:</b> {html.escape(issue.get('ref', ''))} | <b>Nature:</b> {html.escape(str(issue.get('status', '')))}
                        </div>
                        <div style="background-color: #F1F5F9; color: #0F172A; padding: 8px 12px; border-radius: 4px; font-size: 0.9rem; margin-bottom: 8px;">
                            <b>Observation (as presented in draft):</b><br/>{html.escape(str(issue.get('current_disclosure', issue.get('evidence', 'N/A'))))}
                        </div>
                        <div class="correction-box" style="color: #422006;">
                            <b>Suggested correction / disclosure:</b><br/>{html.escape(str(issue.get('suggested_correction', issue.get('action', 'N/A'))))}
                        </div>
                        <div style="font-size: 0.85rem; color: #334155; margin-top: 6px;">
                            <b>Reference:</b> <span style="background-color: #EDE9FE; color: #3B0764; padding: 2px 6px; border-radius: 4px;">{html.escape(issue.get('statutory_ref', 'Reference Verification Required'))}</span>
                        </div>
                        {req_block}
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
