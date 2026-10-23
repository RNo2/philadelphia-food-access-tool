"""Budget planning and a portable, aggregate outcome log."""
import math
import pandas as pd
import plotly.express as px
import streamlit as st
from presentation import export_with_context

STRATEGIES = ["Need first", "Student reach first", "Economic disadvantage first"]
OUTCOME_COLUMNS = ["School ID", "School", "Actual cost ($)", "Students served", "Paired survey responses", "Food insecure before", "Food insecure after", "Notes"]


def allocate(schools, budget, school_cost, capacity, participation):
    """Equal school costs make selecting the top k reach values optimal for reach."""
    if budget < 0 or school_cost <= 0 or capacity < 0 or not 0 <= participation <= 1:
        raise ValueError("Invalid allocation assumptions")
    candidates = schools.copy()
    candidates["Estimated participating students"] = candidates["Enrollment"].fillna(0).clip(lower=0) * participation
    candidates["Economically disadvantaged enrollment estimate"] = candidates["Enrollment"].fillna(0).clip(lower=0) * candidates["Economic %"].fillna(0)
    k = min(math.floor(budget / school_cost), int(capacity), len(candidates))
    orders = {
        "Need first": (["Scenario score", "Economic %", "Enrollment", "School ID"], [False, False, False, True]),
        "Student reach first": (["Estimated participating students", "Scenario score", "School ID"], [False, False, True]),
        "Economic disadvantage first": (["Economically disadvantaged enrollment estimate", "Scenario score", "School ID"], [False, False, True]),
    }
    portfolios = {}
    summaries = []
    for name, (columns, ascending) in orders.items():
        selected = candidates.sort_values(columns, ascending=ascending).head(k).copy()
        selected["Estimated school cost ($)"] = float(school_cost)
        portfolios[name] = selected
        total_students = selected["Enrollment"].sum()
        summaries.append({
            "Strategy": name,
            "Schools": k,
            "Estimated spend ($)": k * school_cost,
            "Unallocated budget ($)": budget - k * school_cost,
            "Estimated participating students": selected["Estimated participating students"].sum(),
            "Economically disadvantaged enrollment estimate": selected["Economically disadvantaged enrollment estimate"].sum(),
            "Enrollment-weighted need score": (selected["Scenario score"] * selected["Enrollment"]).sum() / total_students if total_students > 0 else None,
        })
    return portfolios, pd.DataFrame(summaries)


def outcome_template(portfolio):
    result = portfolio[["School ID", "School"]].copy().reset_index(drop=True)
    for column in OUTCOME_COLUMNS[2:-1]:
        result[column] = float("nan")
    result["Notes"] = ""
    return result


def validate_outcomes(frame, schools):
    missing = set(OUTCOME_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    result = frame[OUTCOME_COLUMNS].copy()
    result["School ID"] = result["School ID"].astype(str)
    if result["School ID"].duplicated().any():
        raise ValueError("Use one aggregate row per school for this evaluation cycle.")
    names = schools.set_index("School ID")["School"]
    if not result["School ID"].isin(names.index).all():
        raise ValueError("Every School ID must belong to the school dataset.")
    result["School"] = result["School ID"].map(names)
    for column in OUTCOME_COLUMNS[2:-1]:
        original = result[column]
        numeric = pd.to_numeric(original, errors="coerce")
        if ((original.notna() & numeric.isna()) | (numeric.notna() & (~numeric.map(lambda x: math.isfinite(x)) | (numeric < 0)))).any():
            raise ValueError(column + " must contain finite, nonnegative numbers or blank cells.")
        if column != "Actual cost ($)" and (numeric.dropna() % 1 != 0).any():
            raise ValueError(column + " must contain whole-number counts.")
        result[column] = numeric
    for column in ["Food insecure before", "Food insecure after"]:
        present = result[column].notna()
        if (present & (result["Paired survey responses"].isna() | (result[column] > result["Paired survey responses"]))).any():
            raise ValueError(column + " cannot exceed paired survey responses; enter the survey count first.")
    if ((result["Paired survey responses"] > result["Students served"]) | (result["Paired survey responses"].notna() & result["Students served"].isna())).any():
        raise ValueError("Paired survey responses require a students-served count and cannot exceed it.")
    return result


def render_budget_lab(schools, all_schools, weights, snapshot):
    st.title("Budget & Allocation Lab")
    st.write("With a limited budget, which schools should outreach reach first? Compare three allocation rules, then collect evidence about what happened.")
    st.info("Planning estimates are not measured benefits. The priority score describes need; enrollment and assumed participation describe potential reach. They do not predict improvements in food security.")
    types_col, levels_col, service_col = st.columns(3)
    types = types_col.multiselect("School type", sorted(schools["Type"].dropna().unique()), key="lab_types")
    levels = levels_col.multiselect("School level", sorted(schools["Level"].dropna().unique()), key="lab_levels")
    statuses = service_col.multiselect("Service status", sorted(schools["Service status"].dropna().unique()), key="lab_service")
    candidates = schools[schools["Type"].isin(types or schools["Type"].dropna().unique()) & schools["Level"].isin(levels or schools["Level"].dropna().unique()) & schools["Service status"].isin(statuses or schools["Service status"].dropna().unique())]
    st.caption(f"{len(candidates):,} matching candidates · Empty filters include all groups. Current service status comes from the supplied service list, not inferred from need scores.")
    plan_tab, outcome_tab = st.tabs(["Plan an allocation", "Record observed outcomes"])
    with plan_tab:
        portfolio = render_allocation_plan(candidates, weights, snapshot)
    with outcome_tab:
        render_outcome_log(portfolio if portfolio is not None else candidates.head(0), all_schools)


def render_allocation_plan(schools, weights, snapshot):
    if schools.empty:
        st.info("No candidates match these filters. Clear a filter to build a plan.")
        return None
    a, b, c, d = st.columns(4)
    budget = a.number_input("Available budget ($)", min_value=0.0, value=None, step=1000.0, key="lab_budget")
    cost = b.number_input("Cost per school per cycle ($)", min_value=1.0, value=None, step=100.0, key="lab_cost")
    capacity = c.number_input("Maximum schools per cycle", min_value=0, max_value=len(schools), value=None, key="lab_capacity")
    rate = d.number_input("Assumed student participation (%)", min_value=0, max_value=100, value=None, key="lab_participation")
    st.caption("Illustrative inputs, not observed program costs. Each school receives one identical-cost outreach cycle; there are no school-specific costs or travel constraints. Participation is assumed equally across schools. Need-first uses the current sidebar weights. Economically disadvantaged enrollment estimates are not participant counts.")
    if any(value is None for value in (budget, cost, capacity, rate)):
        st.info("Enter a budget, cost per school, capacity, and participation assumption to compare allocations.")
        return
    portfolios, summary = allocate(schools, budget, cost, capacity, rate / 100)
    st.subheader("Compare allocation choices")
    st.dataframe(summary, hide_index=True, width="stretch", column_config={
        "Estimated spend ($)": st.column_config.NumberColumn(format="$%.2f"),
        "Unallocated budget ($)": st.column_config.NumberColumn(format="$%.2f"),
        "Estimated participating students": st.column_config.NumberColumn(format="%.1f"),
        "Economically disadvantaged enrollment estimate": st.column_config.NumberColumn(format="%.1f"),
        "Enrollment-weighted need score": st.column_config.NumberColumn(format="%.1f"),
    })
    summary_export = summary.assign(**{"Budget ($)":budget, "School cost ($)":cost, "School capacity":capacity, "Assumed participation (%)":rate, "Candidate schools":len(schools)})
    st.download_button("Download allocation comparison", export_with_context(summary_export, weights, snapshot), "allocation_comparison.csv", "text/csv")
    if summary["Schools"].max() == 0:
        st.warning("No schools can be funded with these inputs. Increase the budget or capacity, or reduce the cost per school.")
    else:
        fig = px.scatter(summary, x="Estimated participating students", y="Enrollment-weighted need score", color="Strategy", hover_data=["Schools", "Estimated spend ($)"], title="Potential reach and need under the same budget")
        st.plotly_chart(fig, width="stretch")
    strategy = st.radio("Portfolio to explore", STRATEGIES, horizontal=True, index=None, key="lab_strategy")
    if strategy is None:
        st.info("Choose a portfolio strategy to explore schools and record outcomes.")
        return
    portfolio = portfolios[strategy]
    selected = summary.set_index("Strategy").loc[strategy]
    max_reach = summary["Estimated participating students"].max()
    st.write(f"**Reach opportunity cost:** this choice has {max_reach - selected['Estimated participating students']:,.1f} fewer estimated participating students than the reach-first allocation. This is a model tradeoff, not a loss of proven benefit.")
    other = portfolios["Student reach first"]
    st.caption(f"{len(set(portfolio['School ID']) & set(other['School ID']))} schools overlap with the reach-first portfolio. Unallocated funds reflect whole-school cost, capacity, or the candidate limit.")
    if "Service status" in portfolio:
        served_count = int(portfolio["Service status"].eq("Currently served").sum())
        if served_count:
            st.caption(f"{served_count} schools in this portfolio are listed as currently served. Use the service-status filter to focus an expansion-only plan.")
    columns = ["School ID", "School", "Type", "Level", "Scenario score", "Enrollment", "Economic %", "Estimated participating students", "Estimated school cost ($)", "Effective fresh miles", "Effective resources", "Food evidence", "Rationale", "Review row"]
    if "Service status" in portfolio:
        columns.append("Service status")
    display = portfolio[columns].copy()
    display["Economic %"] *= 100
    st.dataframe(display, hide_index=True, width="stretch", column_config={"Economic %": st.column_config.NumberColumn(format="%.1f%%")})
    export = display.assign(Strategy=strategy, **{"Budget ($)": budget, "School capacity": capacity, "Assumed participation (%)": rate})
    st.download_button("Download allocation and assumptions", export_with_context(export, weights, snapshot), "budget_allocation.csv", "text/csv")

    return portfolio


def render_outcome_log(portfolio, all_schools):
    st.subheader("Build evidence about actual benefit")
    st.write("Track one evaluation cycle at a time: actual spending, unique students served, and food insecurity before and after among the same survey respondents. Use the same question and follow-up interval across schools.")
    st.caption("Enter aggregate counts only. Keep names and student-level records out of this log. Entries last only for this session; download your CSV to retain them and upload it next time.")
    template = outcome_template(portfolio)
    if portfolio.empty:
        st.caption("No planning portfolio is selected. You can upload an existing outcome CSV or enter school IDs directly; planning assumptions are not required to review actual outcomes.")
    st.download_button("Download blank outcome template", template.to_csv(index=False).encode("utf-8"), "school_outcomes.csv", "text/csv")
    upload = st.file_uploader("Load an outcome CSV for one evaluation cycle", type=["csv"], key="lab_outcome_upload")
    with st.form("lab_outcome_form"):
        edited = st.data_editor(st.session_state.get("lab_outcomes", outcome_template(all_schools.head(0))), num_rows="dynamic", disabled=["School"], hide_index=True, width="stretch")
        save = st.form_submit_button("Calculate observed outcomes")
    if upload is not None and st.button("Import uploaded outcomes"):
        try:
            st.session_state["lab_outcomes"] = validate_outcomes(pd.read_csv(upload, dtype={"School ID": str}), all_schools)
            st.rerun()
        except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
            st.error(str(error))
    if st.button("Use selected portfolio for a new outcome log"):
        if not st.session_state.get("lab_outcomes", pd.DataFrame()).empty:
            st.warning("Download the existing log first, then clear it to begin a new cycle.")
        else:
            st.session_state["lab_outcomes"] = template
            st.rerun()
    if st.button("Clear session outcome log"):
        st.session_state.pop("lab_outcomes", None)
        st.rerun()
    if save:
        try:
            st.session_state["lab_outcomes"] = validate_outcomes(edited, all_schools)
        except ValueError as error:
            st.error(str(error))
    outcomes = st.session_state.get("lab_outcomes")
    if outcomes is not None and not outcomes.empty:
        matched = outcomes.dropna(subset=["Actual cost ($)", "Students served"])
        served = matched["Students served"].sum()
        st.metric("Observed cost per student served", f"${matched['Actual cost ($)'].sum() / served:,.2f}" if served else "Not available")
        st.caption(f"Calculated only from {len(matched)} schools with both actual cost and students-served entries; counts are school-level and may overlap across schools.")
        paired = outcomes.dropna(subset=["Paired survey responses", "Food insecure before", "Food insecure after"])
        n = paired["Paired survey responses"].sum()
        change = 100 * (paired["Food insecure before"].sum() - paired["Food insecure after"].sum()) / n if n else None
        st.metric("Observed reduction in food insecurity", f"{change:.1f} percentage points" if change is not None else "Not available")
        st.caption(f"Based on {int(n)} paired survey responses across {len(paired)} schools. Positive values indicate a reduction; negative values indicate an increase.")
        st.download_button("Save outcome log as CSV", outcomes.to_csv(index=False).encode("utf-8"), "school_outcomes.csv", "text/csv")
    st.write("**Next step for credible impact evidence:** compare the same outcome changes with a similar, not-yet-served group, or use a randomized phased rollout where feasible. Before–after changes alone cannot establish that outreach caused an improvement; seasonality, other programs, and who responds can affect the result.")
