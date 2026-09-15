import hashlib
import io
import random
import time
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

st.set_page_config(
    page_title="ACE Readiness — OctaiPipe",
    page_icon="🟧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Brand styling (OctaiPipe palette)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    :root{
        --orange:#FF7032; --black:#0A0A0A; --grey:#3A3A3A; --offwhite:#F3F1F1;
        --salmon:#FCB79B; --peach:#FED4C2; --blush:#FEE8DF;
        --green:#4E8F2C; --greenbg:#E9F7DE; --red:#B23A2F; --line:#E2DEDC;
    }
    html, body, [class*="css"] { font-family: Arial, "Helvetica Neue", sans-serif; }
    .stApp { background-color: var(--offwhite); }
    .topbar{
        background: var(--black); color: white; padding: 14px 24px;
        border-radius: 8px; margin-bottom: 18px;
        display:flex; justify-content:space-between; align-items:center;
    }
    .topbar b { color: var(--orange); }
    .topbar .env { color:#B9B9B9; font-size: 12px; }
    .card{ background: white; border: 1px solid var(--line); border-radius: 8px;
        padding: 20px 22px; height: 100%; }
    .card h3 { margin-top:0; font-size: 16px; }
    .metric-row{ display:flex; justify-content:space-between; font-size: 14px; margin-bottom: 4px;}
    .tag{ display:inline-block; font-size: 11px; padding: 3px 10px; border-radius: 20px; margin: 4px 6px 0 0;}
    .tag.warn{ background: var(--peach); color: var(--red);}
    .tag.ok{ background: var(--greenbg); color: var(--green);}
    .tier-pill{ display:inline-block; background: var(--blush); color: var(--black);
        font-size: 12px; padding: 4px 12px; border-radius: 20px; margin-bottom: 8px;}
    .price-out { font-size: 34px; margin: 4px 0 0 0; }
    .timeline-out { color: var(--grey); font-size: 13px; margin-bottom: 10px; }
    .credit-box{ background: var(--offwhite); border-radius: 6px; padding: 12px 16px; font-size: 13px; color: var(--grey);}
    .note-box{ background: var(--blush); border-radius: 6px; padding: 12px 16px; font-size: 13px; color: var(--black); margin-bottom: 16px;}
    div.stButton > button {
        background-color: var(--orange); color: var(--black); border: none;
        font-weight: 600; padding: 0.5em 1.3em; border-radius: 6px;
    }
    div.stButton > button:hover { background-color: var(--salmon); color: var(--black); }
</style>
""", unsafe_allow_html=True)


def topbar(env_label="Prototype — internal pitch build"):
    st.markdown(f"""
    <div class="topbar">
        <div><b>OctaiPipe</b> &middot; ACE Readiness Portal</div>
        <div class="env">{env_label}</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "engagements" not in st.session_state:
    st.session_state.engagements = []  # list of dicts
if "current_id" not in st.session_state:
    st.session_state.current_id = None
if "view" not in st.session_state:
    st.session_state.view = "new"  # "new" | "results"

TIERS = [
    (1, "Tier 1 · <1MW", 15000, "5 business days", 4),
    (5, "Tier 2 · 1–5MW", 35000, "8 business days", 8),
    (20, "Tier 3 · 5–20MW", 65000, "12 business days", 12),
    (float("inf"), "Tier 4 · 20MW+", None, "15+ business days, scoped", 16),
]

COMPLIANCE_FRAMEWORKS = {
    "ISO/IEC 27001": {
        "control_area": "Annex A.7 Physical & environmental security · A.8 Asset management",
        "evidence": "Asset register (Brick site model) and environmental monitoring points",
    },
    "SOC 2": {
        "control_area": "Security & Availability Trust Service Criteria (CC6.4, CC7.2, A1.2)",
        "evidence": "BMS environmental monitoring and redundancy evidence",
    },
    "PCI DSS": {
        "control_area": "Requirement 9 — physical access to the cardholder data environment",
        "evidence": "Physical access and environmental control points around CDE zones",
    },
    "HIPAA": {
        "control_area": "Security Rule Physical Safeguards §164.310",
        "evidence": "Facility access, environmental and maintenance records for ePHI hosting areas",
    },
    "GDPR": {
        "control_area": "Article 32 — security & resilience of processing systems",
        "evidence": "Continuous environmental monitoring supporting resilience and incident visibility",
    },
    "NIST SP 800-53 / FedRAMP": {
        "control_area": "PE family — Physical & Environmental Protection (PE-3, PE-13, PE-14, PE-17)",
        "evidence": "Direct BMS point-by-point mapping to the PE control catalog",
    },
    "TIA-942": {
        "control_area": "Tier I–IV infrastructure redundancy rating",
        "evidence": "As-built redundancy (N / N+1 / 2N) assessed directly from the Brick model and BMS",
    },
}

COMPLIANCE_PER_FRAMEWORK_FEE = 4000
COMPLIANCE_BUNDLE_CAP = 18000
COMPLIANCE_EXTRA_DAYS = 2
COMPLIANCE_HOURS_PER_FRAMEWORK = 3


def compliance_addon_price(n_frameworks):
    if n_frameworks == 0:
        return 0
    return min(n_frameworks * COMPLIANCE_PER_FRAMEWORK_FEE, COMPLIANCE_BUNDLE_CAP)


def tier_for(load_mw):
    return next(t for t in TIERS if load_mw <= t[0])


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------
def login_screen():
    topbar("Sign in")
    st.markdown(
        '<div class="note-box">Prototype login — any work email + any password signs you in. '
        "This is a demo of the flow, not production authentication.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("### Sign in to ACE Readiness")
    with st.form("login_form"):
        email = st.text_input("Work email", placeholder="you@company.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        company = st.text_input("Company / site operator name", placeholder="e.g. Meridian Data Centres")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        if not email or "@" not in email:
            st.error("Enter a valid work email to continue.")
        elif not password:
            st.error("Enter a password to continue.")
        else:
            st.session_state.user = {
                "email": email,
                "company": company or email.split("@")[-1].split(".")[0].title(),
            }
            st.rerun()


# ---------------------------------------------------------------------------
# DOCUMENT PROCESSING (derived from real uploads — simulated modelling)
# ---------------------------------------------------------------------------
def count_pdf_pages(uploaded_file):
    if PdfReader is None:
        return 1
    try:
        reader = PdfReader(uploaded_file)
        return max(1, len(reader.pages))
    except Exception:
        return 1


def read_bms_points(uploaded_file):
    """Return a DataFrame of BMS points from a CSV/XLSX upload, or None."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            return pd.read_excel(uploaded_file)
    except Exception:
        return None
    return None


def seeded_rng(*parts):
    key = "|".join(str(p) for p in parts)
    seed = int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


def compliance_status(model_coverage, match_rate, missing_metering, controllers_conflict):
    """Deterministic evidence-readiness status per framework, from the same
    assessment metrics — no separate data collection required."""
    if model_coverage >= 92 and match_rate >= 88:
        return ("ready", "Evidence ready — no gaps blocking this control area.")
    gaps = []
    if missing_metering:
        gaps.append(f"{missing_metering} missing metering point(s)")
    if controllers_conflict:
        gaps.append(f"{controllers_conflict} conflicting controller(s)")
    gap_text = " and ".join(gaps) if gaps else "minor model gaps"
    return ("partial", f"Partial evidence — resolve {gap_text} before this is audit-ready.")


def run_assessment(site_name, it_load_mw, drawing_files, om_files, bms_file, frameworks=None):
    """Simulates the Planner pipeline. Real inputs (page/row counts) drive the
    numbers; coverage, gaps and savings are deterministic pseudo-modelling,
    not the actual Brick-ontology engine."""
    frameworks = frameworks or []
    rng = seeded_rng(site_name, it_load_mw, len(drawing_files), len(om_files),
                      bms_file.name if bms_file else "no-bms")

    # --- Brick site model, driven by real document counts ---
    total_pages = 0
    for f in drawing_files + om_files:
        if f.name.lower().endswith(".pdf"):
            total_pages += count_pdf_pages(f)
        else:
            total_pages += 1  # images / other docs count as one unit each
    total_pages = max(total_pages, 1)
    assets_modelled = int(total_pages * rng.uniform(28, 52))
    drawing_sets = len(drawing_files) + len(om_files)
    model_coverage = round(rng.uniform(84, 97), 1)

    # --- BMS point map, driven by the real uploaded point list if present ---
    bms_df = read_bms_points(bms_file) if bms_file is not None else None
    if bms_df is not None and len(bms_df) > 0:
        points_total = len(bms_df)
    else:
        # no BMS file uploaded — estimate from IT load as a fallback
        points_total = int(it_load_mw * rng.uniform(900, 1300))
    match_rate = round(rng.uniform(80, 94), 1)
    points_reconciled = int(points_total * match_rate / 100)
    points_unmapped = points_total - points_reconciled

    # --- Gap & health report ---
    mislabelled = max(1, int(points_total * rng.uniform(0.004, 0.012)))
    controllers_conflict = max(1, int(assets_modelled * rng.uniform(0.002, 0.006)))
    missing_metering = max(1, int(assets_modelled * rng.uniform(0.005, 0.015)))
    sequence_drift = max(1, int(controllers_conflict * rng.uniform(0.6, 1.4)))

    # --- Optimisation estimate ---
    saving_low = round(rng.uniform(7, 13), 1)
    saving_high = round(saving_low + rng.uniform(3, 6), 1)
    annual_spend_per_mw = 620_000  # assumed cooling energy spend per MW/year
    est_saving_low = int(it_load_mw * annual_spend_per_mw * saving_low / 100)
    est_saving_high = int(it_load_mw * annual_spend_per_mw * saving_high / 100)

    tier_max, tier_name, price, delivery, hours_cap = tier_for(it_load_mw)

    # --- Compliance evidence pack (add-on) ---
    addon_price = compliance_addon_price(len(frameworks))
    addon_hours = len(frameworks) * COMPLIANCE_HOURS_PER_FRAMEWORK
    addon_days = COMPLIANCE_EXTRA_DAYS if frameworks else 0
    compliance_results = {}
    for fw in frameworks:
        status, note = compliance_status(model_coverage, match_rate, missing_metering, controllers_conflict)
        compliance_results[fw] = {
            "status": status,
            "note": note,
            "control_area": COMPLIANCE_FRAMEWORKS[fw]["control_area"],
            "evidence": COMPLIANCE_FRAMEWORKS[fw]["evidence"],
        }

    return {
        "id": f"eng-{int(time.time()*1000)}",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "site_name": site_name,
        "it_load_mw": it_load_mw,
        "tier_name": tier_name,
        "price": price,
        "delivery": delivery,
        "hours_cap": hours_cap,
        "frameworks": frameworks,
        "addon_price": addon_price,
        "addon_hours": addon_hours,
        "addon_days": addon_days,
        "compliance_results": compliance_results,
        "drawing_sets": drawing_sets,
        "total_pages": total_pages,
        "assets_modelled": assets_modelled,
        "model_coverage": model_coverage,
        "points_total": points_total,
        "points_reconciled": points_reconciled,
        "points_unmapped": points_unmapped,
        "match_rate": match_rate,
        "mislabelled": mislabelled,
        "controllers_conflict": controllers_conflict,
        "missing_metering": missing_metering,
        "sequence_drift": sequence_drift,
        "saving_low": saving_low,
        "saving_high": saving_high,
        "est_saving_low": est_saving_low,
        "est_saving_high": est_saving_high,
        "bms_source": "uploaded file" if bms_df is not None else "estimated from IT load (no BMS file uploaded)",
    }


def build_report_markdown(e):
    compliance_section = ""
    if e.get("frameworks"):
        rows = "\n".join(
            f"- **{fw}** ({e['compliance_results'][fw]['control_area']}): "
            f"{e['compliance_results'][fw]['note']}"
            for fw in e["frameworks"]
        )
        compliance_section = f"""
## Compliance evidence pack (add-on)
- Frameworks covered: {', '.join(e['frameworks'])}
- Add-on fee: ${e['addon_price']:,} · adds {e['addon_days']} business days · +{e['addon_hours']} validation hours

{rows}
"""
    return f"""# ACE Readiness — {e['site_name']}

Generated {e['created']} · {e['tier_name']} · IT load {e['it_load_mw']} MW

## Commercial
- Fee: {'${:,}'.format(e['price']) if e['price'] else 'Custom quote'}
- Delivery: {e['delivery']}
- Engineer validation cap: {e['hours_cap']} hours
{compliance_section}
## Brick site model
- Drawing/O&M sets ingested: {e['drawing_sets']}
- Total pages processed: {e['total_pages']}
- Assets modelled: {e['assets_modelled']}
- Model coverage: {e['model_coverage']}%

## BMS point map ({e['bms_source']})
- Total points: {e['points_total']}
- Reconciled: {e['points_reconciled']} ({e['match_rate']}% match)
- Unmapped: {e['points_unmapped']}

## Gap & health report
- Mislabelled sensors: {e['mislabelled']}
- Controllers in conflict: {e['controllers_conflict']}
- Missing metering points: {e['missing_metering']}
- Sequence-drift flags: {e['sequence_drift']}

## Optimisation estimate
- Cooling energy saving: {e['saving_low']}–{e['saving_high']}%
- Estimated annual saving: ${e['est_saving_low']:,}–${e['est_saving_high']:,}
- Costed ACE deployment plan: included

---
*Simulated output for demonstration purposes. Document counts and BMS point
counts are drawn from the files actually uploaded; coverage, gap and saving
figures are modelled, not produced by the production Brick-ontology engine.*
"""


# ---------------------------------------------------------------------------
# NEW ENGAGEMENT
# ---------------------------------------------------------------------------
def new_engagement_screen():
    st.markdown(
        '<div class="note-box">Numbers below are computed from the files you actually upload '
        "(page counts, BMS row counts) combined with a deterministic model — this demonstrates "
        "the flow end to end, but does not run OctaiPipe's production Planner engine.</div>",
        unsafe_allow_html=True,
    )
    st.subheader("New ACE Readiness assessment")

    col1, col2 = st.columns(2)
    with col1:
        site_name = st.text_input("Site name", placeholder="e.g. Jurong West DC-3")
    with col2:
        it_load = st.slider("IT load (MW)", min_value=0.2, max_value=40.0, value=6.0, step=0.1)

    tier_max, tier_name, price, delivery, hours_cap = tier_for(it_load)
    price_display = f"${price:,.0f}" if price else "Custom quote"
    st.markdown(
        f'<span class="tier-pill">{tier_name}</span> '
        f'<span style="margin-left:10px;">Fee: <b>{price_display}</b> &middot; '
        f'Delivery: {delivery} &middot; Validation cap: {hours_cap} hrs</span>',
        unsafe_allow_html=True,
    )

    st.markdown("#### Upload documents")
    d1, d2, d3 = st.columns(3)
    with d1:
        drawing_files = st.file_uploader(
            "M&E drawings & equipment schedules", type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True, key="drawings",
        )
    with d2:
        om_files = st.file_uploader(
            "O&M documents", type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True, key="om",
        )
    with d3:
        bms_file = st.file_uploader(
            "BMS point export (CSV or Excel)", type=["csv", "xlsx", "xls"],
            accept_multiple_files=False, key="bms",
        )

    if bms_file is not None:
        preview = read_bms_points(bms_file)
        if preview is not None:
            st.caption(f"BMS file: {len(preview)} rows detected. Preview:")
            st.dataframe(preview.head(5), use_container_width=True)
        else:
            st.warning("Couldn't parse that BMS file — it'll be excluded and points will be estimated from IT load instead.")

    st.markdown("#### Compliance evidence pack (optional add-on)")
    st.caption(
        "The same Brick model and BMS point map already produced above doubles as physical/environmental "
        "control evidence for these frameworks — no separate data collection. This maps evidence for the "
        "physical & environmental control domains within each framework; it is not a full certification."
    )
    frameworks = st.multiselect(
        "Frameworks to map evidence against",
        options=list(COMPLIANCE_FRAMEWORKS.keys()),
        key="frameworks",
    )
    if frameworks:
        addon_price = compliance_addon_price(len(frameworks))
        st.markdown(
            f'<span class="tier-pill">+{len(frameworks)} framework(s)</span> '
            f'<span style="margin-left:10px;">Add-on fee: <b>${addon_price:,}</b> &middot; '
            f'+{COMPLIANCE_EXTRA_DAYS} business days &middot; '
            f'+{len(frameworks) * COMPLIANCE_HOURS_PER_FRAMEWORK} validation hours</span>',
            unsafe_allow_html=True,
        )

    ready = bool(site_name) and (len(drawing_files or []) + len(om_files or []) > 0)
    if not ready:
        st.caption("Enter a site name and upload at least one drawing or O&M document to run the assessment.")

    if st.button("Run assessment", disabled=not ready, type="primary"):
        drawing_files = drawing_files or []
        om_files = om_files or []
        steps = [
            ("Uploading documents to Planner…", 0.4),
            ("Classifying drawings & schedules…", 0.6),
            ("Building site hierarchy & Brick model…", 0.7),
            ("Reconciling BMS points…", 0.6),
            ("Running engineer validation pass…", 0.5),
            ("Compiling gap & optimisation report…", 0.4),
        ]
        if frameworks:
            steps.append(("Mapping evidence to compliance frameworks…", 0.5))
        progress = st.progress(0.0, text=steps[0][0])
        for i, (label, delay) in enumerate(steps):
            time.sleep(delay)
            progress.progress((i + 1) / len(steps), text=label)
        result = run_assessment(site_name, it_load, drawing_files, om_files, bms_file, frameworks)
        st.session_state.engagements.insert(0, result)
        st.session_state.current_id = result["id"]
        st.session_state.view = "results"
        st.rerun()


# ---------------------------------------------------------------------------
# RESULTS DASHBOARD
# ---------------------------------------------------------------------------
def results_screen(e):
    price_display = f"${e['price']:,.0f}" if e["price"] else "Custom quote"
    total_display = ""
    if e.get("addon_price"):
        total = (e["price"] or 0) + e["addon_price"]
        total_display = f" · with compliance add-on: ${total:,.0f}"
    st.subheader(f"{e['site_name']} — assessment results")
    st.caption(f"{e['tier_name']} · {price_display}{total_display} · delivered in {e['delivery']} · run {e['created']}")

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown('<div class="card"><h3>Brick site model</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Assets modelled</span><b>{e["assets_modelled"]:,}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Drawing sets ingested</span><b>{e["drawing_sets"]}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Pages processed</span><b>{e["total_pages"]}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Model coverage</span><b>{e["model_coverage"]}%</b></div>', unsafe_allow_html=True)
        st.progress(e["model_coverage"] / 100)
        st.markdown('<span class="tag ok">As-designed twin ready</span></div>', unsafe_allow_html=True)

    with d2:
        st.markdown('<div class="card"><h3>BMS point map</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Points reconciled</span><b>{e["points_reconciled"]:,} / {e["points_total"]:,}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>As-controlled match</span><b>{e["match_rate"]}%</b></div>', unsafe_allow_html=True)
        st.progress(e["match_rate"] / 100)
        st.markdown(f'<span class="tag warn">{e["points_unmapped"]} points unmapped</span></div>', unsafe_allow_html=True)
        st.caption(e["bms_source"])

    with d3:
        st.markdown('<div class="card"><h3>Gap & health report</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Mislabelled sensors</span><b>{e["mislabelled"]}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Controllers in conflict</span><b>{e["controllers_conflict"]}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Missing metering points</span><b>{e["missing_metering"]}</b></div>', unsafe_allow_html=True)
        st.markdown(
            f'<span class="tag warn">{e["sequence_drift"]} sequence-drift flags</span>'
            '<span class="tag ok">Full log included</span></div>',
            unsafe_allow_html=True,
        )

    with d4:
        st.markdown('<div class="card"><h3>Optimisation estimate</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Cooling energy saving</span><b>{e["saving_low"]}–{e["saving_high"]}%</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-row"><span>Est. annual saving</span><b>${e["est_saving_low"]:,}–${e["est_saving_high"]:,}</b></div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-row"><span>Costed ACE deployment</span><b>Included</b></div>', unsafe_allow_html=True)
        st.markdown('<span class="tag ok">3 load scenarios modelled</span></div>', unsafe_allow_html=True)

    st.markdown("---")

    if e.get("frameworks"):
        st.markdown("#### Compliance evidence pack")
        st.caption(
            f"Add-on fee ${e['addon_price']:,} · +{e['addon_days']} business days · "
            f"+{e['addon_hours']} validation hours · mapped from the same model above, no extra data collection."
        )
        cols = st.columns(len(e["frameworks"]))
        for col, fw in zip(cols, e["frameworks"]):
            res = e["compliance_results"][fw]
            tag_class = "ok" if res["status"] == "ready" else "warn"
            tag_text = "Evidence ready" if res["status"] == "ready" else "Partial evidence"
            with col:
                st.markdown(
                    f'<div class="card"><h3>{fw}</h3>'
                    f'<div style="font-size:12px;color:#3A3A3A;margin-bottom:8px;">{res["control_area"]}</div>'
                    f'<div style="font-size:13px;margin-bottom:8px;">{res["note"]}</div>'
                    f'<span class="tag {tag_class}">{tag_text}</span></div>',
                    unsafe_allow_html=True,
                )
        st.markdown("---")

    conv = st.selectbox("Expected time to ACE decision", ["Within 6 months", "7–9 months", "After 9 months"], key=f"conv-{e['id']}")
    if conv == "Within 6 months":
        credit = "100% of the fee is credited against year-one ACE spend."
    elif conv == "7–9 months":
        credit = "50% of the fee is credited against year-one ACE spend."
    else:
        credit = "No credit applies — the engagement stands on its own."
    st.markdown(f'<div class="credit-box">{credit}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.download_button(
            "Download report (Markdown)",
            data=build_report_markdown(e),
            file_name=f"ACE_Readiness_{e['site_name'].replace(' ', '_')}.md",
            mime="text/markdown",
        )
    with c2:
        if st.button("Start ACE subscription →"):
            st.success("Credit applied — a solutions engineer will follow up to confirm scope.")
    with c3:
        if st.button("← Back to new assessment"):
            st.session_state.view = "new"
            st.rerun()


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------
if st.session_state.user is None:
    login_screen()
else:
    topbar(f"Signed in as {st.session_state.user['email']} · {st.session_state.user['company']}")

    with st.sidebar:
        st.markdown(f"**{st.session_state.user['company']}**")
        st.caption(st.session_state.user["email"])
        st.markdown("---")
        if st.button("＋ New assessment", use_container_width=True):
            st.session_state.view = "new"
            st.rerun()
        st.markdown("**My assessments**")
        if not st.session_state.engagements:
            st.caption("No assessments run yet this session.")
        for eng in st.session_state.engagements:
            label = f"{eng['site_name']} — {eng['tier_name'].split(' · ')[0]}"
            if st.button(label, key=f"nav-{eng['id']}", use_container_width=True):
                st.session_state.current_id = eng["id"]
                st.session_state.view = "results"
                st.rerun()
        st.markdown("---")
        st.caption("Assessments are stored for this browser session only and are not saved to a database in this prototype.")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.session_state.engagements = []
            st.session_state.current_id = None
            st.session_state.view = "new"
            st.rerun()

    if st.session_state.view == "results" and st.session_state.current_id:
        current = next((e for e in st.session_state.engagements if e["id"] == st.session_state.current_id), None)
        if current:
            results_screen(current)
        else:
            new_engagement_screen()
    else:
        new_engagement_screen()
