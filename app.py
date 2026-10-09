from pathlib import Path
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

BASE = Path(__file__).resolve().parent
DATA_FILE = BASE / "data" / "schools.csv"
SOURCES_FILE = BASE / "data" / "model_sources.csv"
SNAPSHOT_DATE = "October 9, 2026"
BASE_WEIGHTS = {"Economic need": 30.0, "Fresh food access": 25.0, "Resource gap": 25.0, "Potential reach": 5.0}
MAX_POINTS = {"Economic need": 30.0, "Fresh food access": 25.0, "Resource gap": 25.0, "Potential reach": 5.0}

st.set_page_config(page_title="Philadelphia School Food Access Priority Tool", page_icon="◼", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1450px;}
[data-testid="stMetric"] {background:#ffffff; border:1px solid #dde7df; padding:14px 16px; border-radius:14px;}
[data-testid="stSidebar"] {border-right:1px solid #dde7df;}
.hero {padding: 8px 0 14px 0;}
.hero h1 {font-size:2.35rem; line-height:1.08; margin-bottom:.35rem; letter-spacing:-.03em;}
.hero p {font-size:1.03rem; color:#526057; max-width:930px;}
.kicker {font-size:.78rem; letter-spacing:.12em; text-transform:uppercase; color:#2D6A4F; font-weight:700;}
.card {background:white; border:1px solid #dde7df; border-radius:14px; padding:17px 18px; margin-bottom:12px;}
.small {font-size:.84rem; color:#66736a;}
.tier1 {color:#1b5e3a; font-weight:700;}
.tier2 {color:#6c5c00; font-weight:700;}
.tier3 {color:#865200; font-weight:700;}
.tier4 {color:#6c6c6c; font-weight:700;}
hr {border:none; border-top:1px solid #e3e9e4; margin:1.25rem 0;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE, dtype={"School ID": str, "ZIP": str})
    numeric = ["Enrollment","Economic %","Effective fresh miles","Effective resources","Economic points","Fresh points","Resource points","Reach points","Baseline score","Active score","Latitude","Longitude","Rankable"]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

@st.cache_data
def load_sources():
    if SOURCES_FILE.exists():
        return pd.read_csv(SOURCES_FILE)
    return pd.DataFrame(columns=["Setting","Value"])

def normalize_weights(raw):
    total = sum(raw.values())
    if total <= 0:
        return BASE_WEIGHTS.copy()
    return {k: v * 85.0 / total for k, v in raw.items()}

def tier(score):
    if pd.isna(score): return "Missing data"
    if score >= 70: return "Tier 1 — Highest Priority"
    if score >= 55: return "Tier 2 — High Priority"
    if score >= 40: return "Tier 3 — Moderate Priority"
    return "Tier 4 — Lower Priority"

def apply_scenario(df, w):
    out = df.copy()
    out["Scenario score"] = (
        (out["Economic points"] / MAX_POINTS["Economic need"]) * w["Economic need"] +
        (out["Fresh points"] / MAX_POINTS["Fresh food access"]) * w["Fresh food access"] +
        (out["Resource points"] / MAX_POINTS["Resource gap"]) * w["Resource gap"] +
        (out["Reach points"] / MAX_POINTS["Potential reach"]) * w["Potential reach"]
    )
    req = ["Economic points","Fresh points","Resource points","Reach points"]
    out.loc[out[req].isna().any(axis=1), "Scenario score"] = pd.NA
    out["Tier"] = out["Scenario score"].apply(tier)
    out = out.sort_values(["Scenario score","Economic %","Enrollment","School ID"], ascending=[False,False,False,True], na_position="last").reset_index(drop=True)
    out["Scenario rank"] = out["Scenario score"].rank(method="min", ascending=False).astype("Int64")
    return out

def fmt_pct(x):
    return "—" if pd.isna(x) else f"{x:.0%}"

def fmt_num(x, d=0):
    if pd.isna(x): return "—"
    return f"{x:,.{d}f}"

all_df = load_data()

st.sidebar.markdown("### Priority Tool")
page = st.sidebar.radio("Navigate", ["Overview", "Priority Map", "Scenario Lab", "School Explorer", "Methodology & Sources"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption(f"Data snapshot: {SNAPSHOT_DATE}")
st.sidebar.caption("Philadelphia district + charter school targeting model")

eligible_df = all_df[(all_df["Eligible"].astype(str).str.lower() == "yes") & (all_df["Already served"].astype(str).str.lower() != "yes")].copy()

# Shared scenario controls
with st.sidebar.expander("Scenario weights", expanded=(page == "Scenario Lab")):
    st.caption("Change relative importance. We normalize the four values back to an 85-point scale.")
    e = st.slider("Economic need", 0, 60, 30, 1)
    f = st.slider("Fresh food access", 0, 60, 25, 1)
    r = st.slider("Existing-resource gap", 0, 60, 25, 1)
    p = st.slider("Potential reach", 0, 30, 5, 1)
raw_w = {"Economic need":float(e), "Fresh food access":float(f), "Resource gap":float(r), "Potential reach":float(p)}
w = normalize_weights(raw_w)
ranked = apply_scenario(eligible_df, w)
rankable = ranked[ranked["Scenario score"].notna()].copy()

if page == "Overview":
    st.markdown('<div class="hero"><div class="kicker">Applied Economics · Food Access · Resource Allocation</div><h1>Philadelphia School Food Access Priority Tool</h1><p>A transparent decision-support model for identifying schools where fresh-food outreach may have the greatest need. The tool combines economic disadvantage, geographic fresh-food access, nearby food resources, and potential student reach.</p></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Eligible candidates", f"{len(eligible_df):,}")
    c2.metric("Rankable now", f"{len(rankable):,}")
    c3.metric("Tier 1 schools", f"{(rankable['Scenario score']>=70).sum():,}")
    c4.metric("Students in Top 15", f"{int(rankable.head(15)['Enrollment'].sum()):,}")

    st.markdown("### Highest-priority schools")
    top = rankable.head(15).copy()
    show = top[["Scenario rank","School","Type","Economic %","Enrollment","Effective fresh miles","Effective resources","Scenario score","Tier"]].copy()
    show.columns = ["Rank","School","Type","Economic need","Enrollment","Fresh access (mi)","Resources ≤1mi","Score /85","Priority tier"]
    st.dataframe(show, use_container_width=True, hide_index=True,
                 column_config={"Economic need":st.column_config.NumberColumn(format="%.0%%"),"Fresh access (mi)":st.column_config.NumberColumn(format="%.2f"),"Score /85":st.column_config.NumberColumn(format="%.1f")})

    left,right = st.columns([1.1,1])
    with left:
        st.markdown("### What the model is solving")
        st.markdown("""
<div class="card"><b>Scarce-resource allocation problem</b><br><span class="small">If an organization cannot serve every school at once, where should outreach begin? Rankings make that trade-off explicit and reviewable rather than relying on intuition alone.</span></div>
<div class="card"><b>Transparent, adjustable assumptions</b><br><span class="small">Users can change the relative importance of need, access, resource scarcity, and reach. The ranking updates immediately while preserving an 85-point scale.</span></div>
<div class="card"><b>Decision support, not automatic eligibility</b><br><span class="small">Food-access inputs are screening indicators. Staff should verify current conditions, produce quality, hours, recurrence, eligibility, and existing service relationships before committing resources.</span></div>
""", unsafe_allow_html=True)
    with right:
        comp = pd.DataFrame({"Component":list(w.keys()),"Weight":list(w.values())})
        fig = px.bar(comp, x="Weight", y="Component", orientation="h", text=comp["Weight"].map(lambda x:f"{x:.1f}"), title="Current 85-point scenario")
        fig.update_layout(height=320, margin=dict(l=10,r=10,t=50,b=20), yaxis_title=None, xaxis_title="Points")
        st.plotly_chart(fig, use_container_width=True)

elif page == "Priority Map":
    st.markdown('<div class="hero"><div class="kicker">Spatial screening</div><h1>Priority Map</h1><p>Explore where high-priority schools are located and how need changes across the city.</p></div>', unsafe_allow_html=True)
    f1,f2,f3 = st.columns([1.2,1,1])
    with f1:
        types = st.multiselect("School type", sorted(rankable["Type"].dropna().unique()), default=sorted(rankable["Type"].dropna().unique()))
    with f2:
        tiers = st.multiselect("Priority tier", ["Tier 1 — Highest Priority","Tier 2 — High Priority","Tier 3 — Moderate Priority","Tier 4 — Lower Priority"], default=["Tier 1 — Highest Priority","Tier 2 — High Priority"])
    with f3:
        min_econ = st.slider("Minimum economic need", 0, 100, 0, 5)
    m = rankable[rankable["Type"].isin(types) & rankable["Tier"].isin(tiers) & (rankable["Economic %"] >= min_econ/100)].dropna(subset=["Latitude","Longitude"]).copy()
    colors = {"Tier 1 — Highest Priority":[39,105,70,190],"Tier 2 — High Priority":[128,113,27,185],"Tier 3 — Moderate Priority":[181,111,28,175],"Tier 4 — Lower Priority":[110,110,110,160]}
    m["color"] = m["Tier"].map(colors)
    m["radius"] = 90 + m["Scenario score"].fillna(0)*4
    layer = pdk.Layer("ScatterplotLayer", m, get_position="[Longitude, Latitude]", get_fill_color="color", get_radius="radius", pickable=True, auto_highlight=True)
    view = pdk.ViewState(latitude=39.999, longitude=-75.145, zoom=10.4, pitch=0)
    tooltip = {"html":"<b>{School}</b><br/>Score: {Scenario score}<br/>Economic need: {Economic %}<br/>Fresh access: {Effective fresh miles} mi<br/>Resources ≤1mi: {Effective resources}", "style":{"backgroundColor":"#17201A","color":"white"}}
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip), use_container_width=True)
    st.caption(f"Showing {len(m):,} schools. Marker size increases with priority score.")
    st.dataframe(m[["Scenario rank","School","Type","ZIP","Scenario score","Tier"]].head(50), use_container_width=True, hide_index=True,
                 column_config={"Scenario score":st.column_config.NumberColumn(format="%.1f")})

elif page == "Scenario Lab":
    st.markdown('<div class="hero"><div class="kicker">Policy sensitivity</div><h1>Scenario Lab</h1><p>Test how different value judgments change the recommended outreach order. This is the economics layer: the ranking depends on how the organization chooses to value competing objectives.</p></div>', unsafe_allow_html=True)
    st.markdown("#### Normalized scenario weights")
    wc = st.columns(4)
    for col,(name,val) in zip(wc,w.items()): col.metric(name, f"{val:.1f} pts")

    capacity = st.slider("Outreach capacity this cycle (schools)", 1, 50, 15)
    portfolio = rankable.head(capacity)
    a,b,c,d = st.columns(4)
    a.metric("Schools selected", capacity)
    b.metric("Potential student reach", f"{int(portfolio['Enrollment'].sum()):,}")
    c.metric("Avg. economic need", f"{portfolio['Economic %'].mean():.0%}")
    d.metric("Avg. priority score", f"{portfolio['Scenario score'].mean():.1f}/85")

    base = apply_scenario(eligible_df, BASE_WEIGHTS)
    comp = rankable[["School","Scenario rank","Scenario score"]].merge(base[["School","Scenario rank","Scenario score"]], on="School", suffixes=(" current"," baseline"))
    comp["Rank change"] = comp["Scenario rank baseline"] - comp["Scenario rank current"]
    changed = comp.reindex(comp["Rank change"].abs().sort_values(ascending=False).index).head(12)
    st.markdown("### Schools most sensitive to your assumptions")
    fig = px.bar(changed.sort_values("Rank change"), x="Rank change", y="School", orientation="h", title="Rank movement vs. baseline (+ = moves up)")
    fig.update_layout(height=440, margin=dict(l=10,r=10,t=50,b=20), yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("### Recommended portfolio")
    st.dataframe(portfolio[["Scenario rank","School","Type","Economic %","Enrollment","Effective fresh miles","Effective resources","Scenario score","Tier"]], use_container_width=True, hide_index=True,
                 column_config={"Economic %":st.column_config.NumberColumn(format="%.0%%"),"Effective fresh miles":st.column_config.NumberColumn(format="%.2f"),"Scenario score":st.column_config.NumberColumn(format="%.1f")})

elif page == "School Explorer":
    st.markdown('<div class="hero"><div class="kicker">Evidence profile</div><h1>School Explorer</h1><p>Inspect the factors behind an individual school’s ranking and the evidence that should be verified before outreach.</p></div>', unsafe_allow_html=True)
    search = st.text_input("Search school name, ZIP, or School ID", placeholder="e.g., Tacony, 19152, 3404")
    choices = rankable.copy()
    if search.strip():
        q = search.strip().lower()
        mask = choices["School"].str.lower().str.contains(q, na=False) | choices["ZIP"].astype(str).str.contains(q, na=False) | choices["School ID"].astype(str).str.contains(q, na=False)
        choices = choices[mask]
    if choices.empty:
        st.warning("No matching eligible school found.")
    else:
        selected = st.selectbox("School", choices["School"].tolist())
        row = rankable[rankable["School"]==selected].iloc[0]
        st.markdown(f"## {selected}")
        st.caption(f"{row['Type']} · {row['Level']} · ZIP {row['ZIP']} · School ID {row['School ID']}")
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Scenario rank", f"#{int(row['Scenario rank'])}")
        m2.metric("Priority score", f"{row['Scenario score']:.1f}/85")
        m3.metric("Economic need", fmt_pct(row['Economic %']))
        m4.metric("Enrollment", fmt_num(row['Enrollment']))
        left,right = st.columns([1,1])
        with left:
            st.markdown("### Access context")
            st.write(f"**Fresh-food access:** {fmt_num(row['Effective fresh miles'],2)} miles to nearest listed qualifying source")
            st.write(f"**Nearby food resources:** {fmt_num(row['Effective resources'])} within 1 mile")
            st.write(f"**Nearest listed supermarket:** {row['Nearest supermarket'] if pd.notna(row['Nearest supermarket']) else '—'}")
            st.write(f"**Retailer address:** {row['Retailer address'] if pd.notna(row['Retailer address']) else '—'}")
            st.write(f"**School address:** {row['School address'] if pd.notna(row['School address']) else '—'}")
            st.info("Listed access does not establish produce quality, affordability, walkability, hours, recurrence, or household eligibility. Verify before commitment.")
        with right:
            labels=["Economic need","Fresh food access","Resource gap","Potential reach"]
            vals=[row['Economic points']/30*100,row['Fresh points']/25*100,row['Resource points']/25*100,row['Reach points']/5*100]
            fig=go.Figure(go.Bar(x=vals,y=labels,orientation='h',text=[f"{v:.0f}%" for v in vals],textposition='auto'))
            fig.update_layout(title="Rubric strength by component",xaxis=dict(range=[0,100],title="Share of maximum component points"),yaxis_title=None,height=320,margin=dict(l=10,r=10,t=50,b=25))
            st.plotly_chart(fig,use_container_width=True)
        st.markdown("### Why it ranks here")
        st.markdown(f'<div class="card">{row["Rationale"]}</div>', unsafe_allow_html=True)

elif page == "Methodology & Sources":
    st.markdown('<div class="hero"><div class="kicker">Transparency</div><h1>Methodology & Sources</h1><p>The model is intentionally simple enough for staff to audit. Each component is scored from observable indicators, then combined into an 85-point priority score.</p></div>', unsafe_allow_html=True)
    st.markdown("### Baseline rubric")
    rubric = pd.DataFrame([
        ["Economic need",30,"90%+ → 30; 80–89.9 → 25; 70–79.9 → 20; 60–69.9 → 15; 50–59.9 → 10; 40–49.9 → 5; below 40 → 0"],
        ["Fresh food access",25,">1 mi → 25; 0.75–1 → 20; 0.50–0.74 → 15; 0.25–0.49 → 10; <0.25 → 5"],
        ["Existing food-access resources",25,"0 → 25; 1 → 20; 2 → 15; 3 → 10; 4 → 5; 5+ → 0"],
        ["Potential reach / enrollment",5,"700+ → 5; 500–699 → 4; 350–499 → 3; 200–349 → 2; under 200 → 1"],
    ], columns=["Component","Maximum points","Scoring rule"])
    st.dataframe(rubric,use_container_width=True,hide_index=True)
    st.markdown("### Priority tiers")
    st.write("**Tier 1:** 70–85 · **Tier 2:** 55–69 · **Tier 3:** 40–54 · **Tier 4:** 0–39")
    st.markdown("### Ranking rule")
    st.write("Scores are sorted descending, then economic disadvantage descending, enrollment descending, and School ID ascending. Schools missing a required input remain visible in the source model but are not given a complete scenario score.")
    st.markdown("### Data provenance")
    st.write(f"This public tool uses the model snapshot dated **{SNAPSHOT_DATE}**. Directory data are 2026–27; enrollment/demographic inputs are 2025–26. Charter Title I status uses the last populated 2025–26 designation where the current directory omits it and should be confirmed before commitment.")
    src=load_sources()
    links=src[src['Setting'].astype(str).str.contains('URL',case=False,na=False)].copy()
    if not links.empty:
        st.dataframe(links.rename(columns={"Setting":"Source","Value":"URL"}),use_container_width=True,hide_index=True)
    st.markdown("### Important limitations")
    st.markdown("""
- Geographic proximity is a screening proxy, not proof of affordable or practical access.
- A listed food site may have limited hours, recurrence, eligibility rules, or changing operations.
- “Already served = No” means unchecked unless staff explicitly verified service history.
- The tool prioritizes outreach; it does not determine legal/program eligibility and should not replace field verification.
- Weight changes represent value judgments. They are useful for sensitivity analysis, not a claim that one set of weights is objectively correct.
""")

st.markdown("---")
st.caption("Decision-support prototype built from the SBD Expansion Model. Public-facing outputs should be paired with staff verification and periodic data refreshes.")
