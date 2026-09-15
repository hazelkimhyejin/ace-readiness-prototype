import streamlit as st

st.set_page_config(
    page_title="ACE Readiness — OctaiPipe",
    page_icon="🟧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Brand styling (OctaiPipe palette) injected as CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    :root{
        --orange:#FF7032; --black:#0A0A0A; --grey:#3A3A3A; --offwhite:#F3F1F1;
        --salmon:#FCB79B; --peach:#FED4C2; --blush:#FEE8DF;
        --green:#4E8F2C; --greenbg:#E9F7DE; --red:#B23A2F; --line:#E2DEDC;
    }
    html, body, [class*="css"]  { font-family: Arial, "Helvetica Neue", sans-serif; }
    .stApp { background-color: var(--offwhite); }

    .topbar{
        background: var(--black); color: white; padding: 14px 24px;
        border-radius: 8px; margin-bottom: 18px;
        display:flex; justify-content:space-between; align-items:center;
    }
    .topbar b { color: var(--orange); }
    .topbar .env { color:#B9B9B9; font-size: 12px; }

    .hero h1 { font-weight:400; font-size: 40px; line-height:1.25; margin-bottom: 10px; }
    .hero p.sub { color: var(--grey); font-size: 16px; max-width: 640px; }

    .stat-num { color: var(--orange); font-size: 30px; }
    .stat-lbl { color: var(--grey); font-size: 13px; }

    .card{
        background: white; border: 1px solid var(--line); border-radius: 8px;
        padding: 20px 22px; height: 100%;
    }
    .card h3 { margin-top:0; font-size: 16px; }
    .metric-row{ display:flex; justify-content:space-between; font-size: 14px; margin-bottom: 4px;}

    .tag{ display:inline-block; font-size: 11px; padding: 3px 10px; border-radius: 20px; margin: 4px 6px 0 0;}
    .tag.warn{ background: var(--peach); color: var(--red);}
    .tag.ok{ background: var(--greenbg); color: var(--green);}

    .tier-pill{ display:inline-block; background: var(--blush); color: var(--black);
        font-size: 12px; padding: 4px 12px; border-radius: 20px; margin-bottom: 8px;}

    .price-out { font-size: 38px; margin: 4px 0 0 0; }
    .timeline-out { color: var(--grey); font-size: 13px; margin-bottom: 14px; }

    .credit-box{ background: var(--offwhite); border-radius: 6px; padding: 14px 16px; font-size: 13px; color: var(--grey);}

    .step-n{ color: var(--orange); font-size: 13px; margin-bottom:4px;}
    .step h4{ margin: 0 0 4px 0; font-size: 14px;}
    .step p{ color: var(--grey); font-size: 13px; margin:0;}

    .cta-box{ background: var(--black); color: white; border-radius: 10px; padding: 30px 36px; }
    .cta-box p { color: #C9C9C9; font-size: 14px; }

    .footer-col h5{ font-size: 12px; margin-bottom: 6px; }
    .footer-col p{ font-size: 12px; color: var(--grey); }

    div.stButton > button {
        background-color: var(--orange); color: var(--black); border: none;
        font-weight: 600; padding: 0.6em 1.4em; border-radius: 6px;
    }
    div.stButton > button:hover { background-color: var(--salmon); color: var(--black); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
st.markdown("""
<div class="topbar">
    <div><b>OctaiPipe</b> &middot; ACE Readiness Portal</div>
    <div class="env">Prototype &mdash; internal pitch build</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>A machine-readable model of your site,<br>delivered before you commit to anything.</h1>
    <p class="sub">ACE Readiness turns the site assessment you're already paying someone for into a
    fixed-fee, fast-turnaround engagement &mdash; and credits the fee back if you move to ACE.</p>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
for col, num, lbl in [
    (c1, "5&ndash;15", "business days to delivery"),
    (c2, "100%", "fee credited within 6 months"),
    (c3, "4", "deliverables, one engagement"),
]:
    with col:
        st.markdown(f'<div class="stat-num">{num}</div><div class="stat-lbl">{lbl}</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# 1. Pricing calculator
# ---------------------------------------------------------------------------
st.subheader("1. Price your site")
st.caption("Pricing is banded by IT load. Move the slider to see the tier, fee, and delivery window for a site like yours.")

TIERS = [
    (1,  "Tier 1 · <1MW",    15000, "5 business days"),
    (5,  "Tier 2 · 1–5MW",   35000, "8 business days"),
    (20, "Tier 3 · 5–20MW",  65000, "12 business days"),
    (float("inf"), "Tier 4 · 20MW+", None, "15+ business days, scoped"),
]

left, right = st.columns([1, 1])
with left:
    load = st.slider("IT load (MW)", min_value=0.2, max_value=40.0, value=3.0, step=0.1)
    conv = st.selectbox(
        "Expected time to ACE decision",
        ["Within 6 months", "7–9 months", "After 9 months"],
    )

tier_name, price, days = next((t[1], t[2], t[3]) for t in TIERS if load <= t[0])

with right:
    st.markdown(f'<span class="tier-pill">{tier_name}</span>', unsafe_allow_html=True)
    price_display = f"${price:,.0f}" if price else "Custom quote"
    st.markdown(f'<div class="price-out">{price_display}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="timeline-out">Delivered in {days}</div>', unsafe_allow_html=True)

    if conv == "Within 6 months":
        credit_text = "If you sign an ACE subscription <b>within 6 months</b>, the full fee is credited against year-one ACE spend."
    elif conv == "7–9 months":
        credit_text = "Signing between <b>7 and 9 months</b> credits half the fee against year-one ACE spend."
    else:
        credit_text = "Outside 9 months, the engagement stands on its own &mdash; no credit applies, no obligation either way."
    st.markdown(f'<div class="credit-box">{credit_text}</div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# 2. Sample deliverables
# ---------------------------------------------------------------------------
st.subheader("2. What you get")
st.caption("Sample output from a completed engagement — a 6MW colo site, ingested from M&E drawings, "
           "equipment schedules and 90 days of BMS trend data.")

d1, d2, d3, d4 = st.columns(4)

with d1:
    st.markdown('<div class="card"><h3>Brick site model</h3>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Assets modelled</span><b>1,842</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Drawing sets ingested</span><b>37</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Model coverage</span><b>94%</b></div>', unsafe_allow_html=True)
    st.progress(0.94)
    st.markdown('<span class="tag ok">As-designed twin ready</span></div>', unsafe_allow_html=True)

with d2:
    st.markdown('<div class="card"><h3>BMS point map</h3>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Points reconciled</span><b>6,210 / 6,600</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>As-controlled match</span><b>88%</b></div>', unsafe_allow_html=True)
    st.progress(0.88)
    st.markdown('<span class="tag warn">390 points unmapped</span></div>', unsafe_allow_html=True)

with d3:
    st.markdown('<div class="card"><h3>Gap &amp; health report</h3>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Mislabelled sensors</span><b>54</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Controllers in conflict</span><b>9</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Missing metering</span><b>22</b></div>', unsafe_allow_html=True)
    st.markdown('<span class="tag warn">9 sequence-drift flags</span>'
                '<span class="tag ok">Full log included</span></div>', unsafe_allow_html=True)

with d4:
    st.markdown('<div class="card"><h3>Optimisation estimate</h3>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Cooling energy saving</span><b>11–16%</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Est. annual saving</span><b>$310k–$450k</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="metric-row"><span>Costed ACE deployment</span><b>Included</b></div>', unsafe_allow_html=True)
    st.markdown('<span class="tag ok">3 load scenarios modelled</span></div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# 3. Delivery journey
# ---------------------------------------------------------------------------
st.subheader("3. How it's delivered")
st.caption("Planner does the ingestion and modelling. A named engineer validates it — capped hours, so the fee stays fixed.")

j1, j2, j3, j4 = st.columns(4)
steps = [
    (j1, "Day 0–1", "Document intake", "Drawings, schedules and O&M docs uploaded to Planner; BMS export connected read-only."),
    (j2, "Day 1–3", "Automated modelling", "Planner classifies documents, builds the site hierarchy, and maps points into Brick — unattended."),
    (j3, "Day 3–5", "Engineer validation", "Capped review window (4–16 hrs by tier) to resolve ambiguous mappings and sanity-check the gap list."),
    (j4, "Day 5–15", "Handover", "Report and portal access delivered direct, or via a certified partner for site-walk-dependent tiers."),
]
for col, n, title, desc in steps:
    with col:
        st.markdown(f'<div class="step"><div class="step-n">{n}</div><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# 4. Conversion CTA
# ---------------------------------------------------------------------------
cta_l, cta_r = st.columns([3, 1])
with cta_l:
    st.markdown("""
    <div class="cta-box">
        <h2 style="margin-top:0;">Ready to convert?</h2>
        <p>Your ACE Readiness fee is held as a credit for 6 months from delivery. Converting inside that
        window applies it in full against year-one ACE subscription.</p>
    </div>
    """, unsafe_allow_html=True)
with cta_r:
    st.write("")
    st.write("")
    if st.button("Start ACE subscription →"):
        st.success("Credit applied — a solutions engineer will follow up to confirm scope.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown('<div class="footer-col"><h5>Who buys this</h5>'
                '<p>Facilities & critical engineering leads booking asset registers or BMS audits; '
                'sustainability leads preparing ISO 50001 / EED reporting; M&A teams needing site due '
                'diligence — with or without an ACE decision on the table.</p></div>', unsafe_allow_html=True)
with f2:
    st.markdown('<div class="footer-col"><h5>Who owns what</h5>'
                '<p>OctaiPipe owns the Planner tooling and the underlying model. The customer receives the '
                'report and read-only portal access; the twin becomes the live operating model on ACE '
                'conversion.</p></div>', unsafe_allow_html=True)
with f3:
    st.markdown('<div class="footer-col"><h5>Who can sell it</h5>'
                '<p>Direct for Tier 3–4 sites. ABB, CBRE, Datalec and Italtel can deliver Tier 1–2 self-serve '
                'through a partner portal, on a revenue share.</p></div>', unsafe_allow_html=True)

st.caption("OctaiPipe internal prototype · built for the Monetising Pre-Sales hackathon · not for external distribution")
