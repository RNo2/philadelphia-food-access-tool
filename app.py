from pathlib import Path
import math
from html import escape
from budget_lab import render_budget_lab
from food_evidence import render_food_sites
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

def filter_schools(df, key, tier_options=None):
    query = st.text_input("Search school name, ZIP, or School ID", key=key + "_search")
    a, b, c = st.columns(3)
    with a:
        types = st.multiselect("School type", sorted(df["Type"].dropna().unique()), default=sorted(df["Type"].dropna().unique()), key=key + "_types")
    with b:
        levels = st.multiselect("School level", sorted(df["Level"].dropna().unique()), default=sorted(df["Level"].dropna().unique()), key=key + "_levels")
    with c:
        options = tier_options if tier_options is not None else sorted(df["Tier"].unique())
        tiers = st.multiselect("Priority tier", options, default=options, key=key + "_tiers")
    out = df[df["Type"].isin(types) & df["Level"].isin(levels) & df["Tier"].isin(tiers)]
    if query.strip():
        match = pd.Series(False, index=out.index)
        for column in ["School", "ZIP", "School ID"]:
            match |= out[column].astype(str).str.contains(query.strip(), case=False, regex=False, na=False)
        out = out[match]
    return out.copy()


def school_table(df, filename):
    columns = ["Scenario rank", "School", "Type", "Level", "School ID", "ZIP", "School address", "Enrollment", "Economic %", "Scenario score", "Tier", "Effective fresh miles", "Effective resources", "Food evidence", "Rationale", "Review row", "Order"]
    table = df[columns].rename(columns={"Type": "School type", "Level": "School level", "Economic %": "Economic need", "Scenario score": "Score /85", "Effective fresh miles": "Fresh miles", "Effective resources": "Resources ≤1mi", "Rationale": "Why it needs attention"})
    # Display percentages as 0–100 while keeping model values unchanged.
    table["Economic need"] *= 100
    st.dataframe(table, use_container_width=True, hide_index=True,
                 column_config={"Economic need": st.column_config.NumberColumn(format="%.1f%%"), "Score /85": st.column_config.NumberColumn(format="%.1f")})
    st.download_button("Download filtered schools", table.to_csv(index=False).encode("utf-8"), filename, "text/csv")
    if table.empty:
        st.info("No rankable schools match these filters.")


all_df = load_data()

st.sidebar.markdown("### Priority Tool")
page = st.sidebar.radio("Navigate", ["Overview", "All Rankable Schools", "Served Schools", "Food Resources", "Priority Map", "Budget & Allocation Lab", "Scenario Lab", "School Explorer", "Methodology & Sources"], label_visibility="collapsed")
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
ranked["Order"] = range(1, len(ranked) + 1)
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
    show["Economic need"] *= 100
    for column, field in [("Order", "Order"), ("School level", "Level"), ("Food evidence", "Food evidence"), ("Why it needs attention", "Rationale"), ("Review row", "Review row")]:
        show[column] = top[field]
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

elif page == "All Rankable Schools":
    st.title("All Rankable Schools")
    st.write("Every eligible, unserved school with a complete scenario score. Rankings follow your sidebar weights.")
    st.caption("School level describes grades served; school type describes district, charter, or contracted status. Combined levels are retained exactly as listed in the source.")
    schools = filter_schools(rankable, "directory")
    a, b, c = st.columns(3)
    a.metric("Schools shown", len(schools))
    b.metric("Total rankable schools", len(rankable))
    c.metric("Students in filtered schools", fmt_num(schools["Enrollment"].sum()))
    school_table(schools, "rankable_schools.csv")

elif page == "Served Schools":
    st.title("Served Schools")
    st.write("See where schools in your SY26–27 service list land under the current scenario weights.")
    st.caption("Ranks use the same eligible-school comparison pool as All Rankable Schools, including the served schools in this list. Changing sidebar weights recalculates scores and ranks. This page does not change the existing rankings or allocation candidates.")
    service = pd.read_csv(BASE / "data" / "served_schools.csv", dtype={"School ID": str})
    scored = apply_scenario(all_df, w).drop(columns=["Scenario rank"])
    scored["Scenario rank"] = scored["School ID"].map(rankable.set_index("School ID")["Scenario rank"]).astype("Int64")
    served = service.merge(scored, on="School ID", how="left", validate="one_to_one", indicator=True)
    active = served[served["Service status"] == "Currently served"]
    a, b, c, d = st.columns(4)
    a.metric("Currently served schools", len(active))
    b.metric("Formerly served schools", int((served["Service status"] == "Formerly served").sum()))
    c.metric("Current schools with a scenario rank", int(active["Scenario rank"].notna().sum()))
    d.metric("Enrollment at current schools", fmt_num(active["Enrollment"].sum()))
    status = st.radio("Service group", ["Currently served", "Formerly served", "All listed schools"], horizontal=True)
    subset = served if status == "All listed schools" else served[served["Service status"] == status]
    unmatched = subset[subset["_merge"] == "left_only"]
    if not unmatched.empty:
        st.warning("These source schools could not be matched; no rank or score has been inferred.")
        st.dataframe(unmatched[["Source school name", "Service status"]], hide_index=True)
    matched = served[served["_merge"] == "both"].copy()
    st.caption("Former service comes from the sheet’s ‘No longer serving’ section. Enrollment and need values come from the model snapshot, not the service sheet. Service status does not demonstrate an improvement in food security.")
    choices = filter_schools(matched, "served", [tier(85), tier(60), tier(45), tier(0), "Missing data"])
    if status != "All listed schools":
        choices = choices[choices["Service status"] == status]
    choices = choices.sort_values(["Scenario rank", "School"], na_position="last")
    table = choices[["Scenario rank", "School", "Type", "Level", "School ID", "ZIP", "School address", "Enrollment", "Economic %", "Scenario score", "Tier", "Service status", "Effective fresh miles", "Effective resources", "Food evidence", "Rationale", "Review row"]].rename(columns={"Type": "School type", "Level": "School level", "Economic %": "Economic need", "Scenario score": "Score /85", "Effective fresh miles": "Fresh miles", "Effective resources": "Resources ≤1mi", "Rationale": "Why it needs attention"})
    table["Economic need"] *= 100
    st.dataframe(table, hide_index=True, use_container_width=True, column_config={"Economic need": st.column_config.NumberColumn(format="%.2f%%"), "Score /85": st.column_config.NumberColumn(format="%.1f")})
    st.download_button("Download served-school rankings", table.to_csv(index=False).encode("utf-8"), "served_school_rankings.csv", "text/csv")
    if choices.empty:
        st.info("No served schools match these filters.")
    else:
        chart = choices.dropna(subset=["Scenario score"])
        if not chart.empty:
            st.plotly_chart(px.bar(chart.sort_values("Scenario score"), x="Scenario score", y="School", color="Service status", orientation="h", title="Priority scores across your service footprint", hover_data=["Scenario rank", "Level", "Tier"]), use_container_width=True)
        if choices["Scenario rank"].isna().any():
            st.info("A blank scenario rank means the school is outside the current rankable comparison pool or lacks required scoring data.")
    with st.expander("Source and school-name matching"):
        st.write("Source: SBD SY26x27 School Master Sheet, supplied October 14, 2026. Abbreviated names were resolved against school names and addresses; John B. Kelly was matched by name. Staff contacts and internal operational notes are omitted.")
        st.dataframe(subset[["Source school name", "School", "School ID", "Service status", "Match basis"]], hide_index=True, use_container_width=True)

elif page == "Food Resources":
    st.title("Food Resources")
    st.write("Find food assistance through these three directories, then review the school-level food-access evidence used by this model.")
    directories = [
        ("City of Philadelphia", "https://www.phila.gov/food/", "City food-access information and food-finding resources."),
        ("Philabundance", "https://www.philabundance.org/find-food-food-map/", "Philabundance’s food map for locating food assistance."),
        ("Share Food Program", "https://www.sharefoodprogram.org/find-food/find-a-food-site/", "Share Food Program’s food-site finder."),
    ]
    for col, (name, url, description) in zip(st.columns(3), directories):
        with col:
            st.subheader(name)
            st.write(description)
            st.link_button("Open " + name + " directory", url)
    st.info("These links open the providers’ directories. Food-site listings are imported from the supplied workbook snapshot; current hours and eligibility have not been verified here. Check the provider’s current listing before visiting; the school evidence below is from the October 9, 2026 model snapshot.")
    st.subheader("Food access around schools")
    schools = filter_schools(rankable, "food")
    cols = ["School", "Type", "Level", "ZIP", "Nearest supermarket", "Retailer address", "Effective fresh miles", "Effective resources", "Fresh basis", "Resource basis", "Food evidence"]
    evidence = schools[cols].rename(columns={"Type": "School type", "Level": "School level", "Effective fresh miles": "Fresh access (mi)", "Effective resources": "Resources within 1 mi"})
    st.caption(f"{len(evidence):,} schools. Retailers are listed supermarket evidence, not confirmed free-food distribution sites. Resource counts are snapshot indicators. Select a school below for named nearby food sites and website references.")
    st.dataframe(evidence, hide_index=True, use_container_width=True,
                 column_config={"Fresh access (mi)": st.column_config.NumberColumn(format="%.2f")})
    st.download_button("Download food-access evidence", evidence.to_csv(index=False).encode("utf-8"), "school_food_evidence.csv", "text/csv")
    if schools.empty:
        st.warning("No schools match these filters.")
    else:
        school_id = st.selectbox("School evidence profile", schools["School ID"].tolist(),
                                 format_func=lambda sid: schools.set_index("School ID").loc[sid, "School"] + " · " + sid)
        row = schools.set_index("School ID").loc[school_id]
        st.write(f"**{row['School']}** · {row['Level']} · {row['Type']} · ZIP {row['ZIP']}")
        for label, field in [("Nearest listed supermarket", "Nearest supermarket"), ("Retailer address", "Retailer address"), ("Fresh-food evidence basis", "Fresh basis"), ("Resource evidence basis", "Resource basis"), ("Food evidence", "Food evidence")]:
            st.write(f"**{label}:** {row[field] if pd.notna(row[field]) else 'Not recorded'}")
        render_food_sites(row, "food_profile_sites")

elif page == "Priority Map":
    st.title("Priority Map")
    st.write("Filter all rankable schools, explore their priority and food-access context, and focus on an individual school.")
    schools = filter_schools(rankable, "map")
    min_econ = st.slider("Minimum economic need", 0, 100, 0, 5)
    schools = schools[schools["Economic %"] >= min_econ / 100].copy()
    valid = schools["Latitude"].between(-90, 90) & schools["Longitude"].between(-180, 180)
    m = schools[valid].copy()
    a, b, c = st.columns(3)
    a.metric("Mapped schools", len(m))
    b.metric("Without valid coordinates", len(schools) - len(m))
    c.metric("Students at mapped schools", fmt_num(m["Enrollment"].sum()))
    st.caption("● Green: Tier 1 (≥70) · Gold: Tier 2 (55–<70) · Orange: Tier 3 (40–<55) · Gray: Tier 4 (<40). Marker size follows priority score.")
    if m.empty:
        st.warning("No schools with valid coordinates match these filters. Adjust the filters to show schools.")
    else:
        focus = st.selectbox("Focus on a school", [""] + m["School ID"].tolist(),
                             format_func=lambda sid: "All filtered schools" if not sid else m.set_index("School ID").loc[sid, "School"] + " · " + sid)
        labels = st.checkbox("Show school names", value=False)
        style = st.selectbox("Map background", ["Light", "Dark", "Street"])
        colors = {"Tier 1 — Highest Priority": [39,105,70,210], "Tier 2 — High Priority": [128,113,27,210], "Tier 3 — Moderate Priority": [181,111,28,210], "Tier 4 — Lower Priority": [110,110,110,210]}
        m["color"] = m["Tier"].map(colors)
        m["radius"] = 90 + m["Scenario score"] * 4
        for target, source in [("school_label", "School"), ("level_label", "Level"), ("type_label", "Type"), ("address_label", "School address"), ("supermarket_label", "Nearest supermarket"), ("tier_label", "Tier")]:
            m[target] = m[source].fillna("Not recorded").astype(str).map(escape)
        m["score_label"] = m["Scenario score"].map(lambda x: f"{x:.1f}/85")
        m["econ_label"] = m["Economic %"].map(fmt_pct)
        m["fresh_label"] = m["Effective fresh miles"].map(lambda x: fmt_num(x, 2))
        m["resource_label"] = m["Effective resources"].map(fmt_num)
        layers = [pdk.Layer("ScatterplotLayer", m, id="schools", get_position="[Longitude, Latitude]", get_fill_color="color", get_radius="radius", radius_min_pixels=5, radius_max_pixels=22, pickable=True, auto_highlight=True)]
        if labels:
            layers.append(pdk.Layer("TextLayer", m, id="school-names", get_position="[Longitude, Latitude]", get_text="School", get_size=12, get_color=[30,80,55], get_pixel_offset=[0,-18]))
        if focus:
            selected = m[m["School ID"] == focus]
            row = selected.iloc[0]
            layers.append(pdk.Layer("ScatterplotLayer", selected, id="selected-school", get_position="[Longitude, Latitude]", get_radius=500, filled=False, stroked=True, get_line_color=[30,90,220], line_width_min_pixels=3))
            view = pdk.ViewState(latitude=float(row["Latitude"]), longitude=float(row["Longitude"]), zoom=14)
            st.write(f"**{row['School']}** · {row['Level']} · {row['Type']} · {row['School address']}")
            st.caption("Blue outline identifies the selected school; it does not represent a service area.")
        else:
            view = pdk.data_utils.compute_view(m[["Longitude", "Latitude"]], view_proportion=0.85) if len(m) > 1 else pdk.ViewState(latitude=float(m.iloc[0]["Latitude"]), longitude=float(m.iloc[0]["Longitude"]), zoom=13)
        tooltip = {"html": "<b>{school_label}</b><br/>{level_label} · {type_label}<br/>{address_label}<br/>{tier_label}<br/>Score: {score_label}<br/>Economic need: {econ_label}<br/>Fresh access: {fresh_label} mi<br/>Resources within 1 mi: {resource_label}<br/>Nearest listed supermarket: {supermarket_label}", "style": {"backgroundColor": "#17201A", "color": "white"}}
        styles = {"Light": "light", "Dark": "dark", "Street": "road"}
        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view, tooltip=tooltip, map_provider="carto", map_style=styles[style]), use_container_width=True)
        st.caption("Pan and zoom to explore; hover over a marker for school and food-access details. Map backgrounds require internet access. See Food Resources or School Explorer for nearby food-site listings from the workbook snapshot; consult providers for current availability.")
    school_table(schools, "mapped_school_selection.csv")

elif page == "Budget & Allocation Lab":
    render_budget_lab(rankable, all_df)

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
    st.dataframe(portfolio[["Scenario rank","School","Type","Level","Economic %","Enrollment","Effective fresh miles","Effective resources","Scenario score","Tier","Food evidence","Rationale","Review row"]], use_container_width=True, hide_index=True,
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
        render_food_sites(row, "explorer_food_sites")
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
