# Philadelphia School Food Access Priority Tool

A public decision-support app for reviewing school-level food-access need,
comparing outreach allocations, and collecting evidence about actual outcomes.
It is built with Streamlit and the supplied SBD Expansion Model.

## Run locally

Python 3.12 was validated. From the repository directory:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Run from this directory so Streamlit loads `.streamlit/config.toml`, which enables
the green/ivory theme and serves the page artwork from `static/`. No database or
API key is required. Streamlit 1.65 or newer is required for the layout API.

## Review workflow

1. **Overview:** filter by school type, grade level, and service status. See the
   highest-priority matching schools (25 by default, adjustable), then download
   the shortlist and a concise review brief with the snapshot and scenario weights.
2. **School Explorer / Food Resources:** inspect component contributions,
   supermarket evidence, nearby named food sites, addresses, and provider links.
3. **Distance review:** compare up to 25 schools after filtering; inspect pairwise
   distances or request a rubric-priority shortlist with minimum school spacing.
4. **Budget & Allocation Lab:** compare need, reach, and disadvantaged-enrollment
   strategies. The separate outcomes tab works without hypothetical budget inputs.

The app also includes **All Rankable Schools**, **Served Schools**, the original
**Priority Map**, **Scenario Lab**, a concise **Methodology & Sources** page with
an original-workbook download, and a final **Analytical Framework** page.

## Model and inputs

- The four baseline component maxima are 30 (economic need), 25 (fresh access),
  25 (resource gap), and 5 (potential reach). Scenario weights normalize to 85.
- Every input/filter box starts blank in a fresh session. Empty filters include
  all matches. Blank weight fields use baseline values; all-zero entries restore
  baseline weights. Budget calculations require explicit assumptions.
- Filters apply before top-N limits. Displayed ranks remain relative to the
  citywide eligible comparison pool; tied scores share a rank, while Order is
  sequential. Missing component points are not imputed.
- Service status is joined by School ID from the supplied crosswalk, distinguishing
  15 currently served and 3 formerly served schools. "Not listed as served" is
  not proof of no historical service. Existing citywide rank references are
  retained. All groups are available until a service-status filter is selected.
- Need scores are planning indicators, not measured benefit, causal treatment
  effects, or automatic eligibility decisions. Enrollment is potential reach.

## Data and provenance

`data/schools.csv` is the saved October 9, 2026 model snapshot. Directory data are
2026–27; enrollment/demographic inputs use 2025–26 published files. Original source
references are in `data/model_sources.csv`. Opening the app does not refresh data.

`data/food_sites.csv` contains 309 public food-site listings extracted from the
October 20 workbook; government-source retrieval was recorded as October 9.
Nearby-site tables recompute Haversine distances for each selected school and
include only active candidate Food Sites within one mile, excluding recorded
closures. Multiple listings can share an address, so listing counts can differ
from the model's distinct-address resource count.

Fresh-food scoring currently covers the saved USDA supermarket/superstore feed.
Broader coverage of farmers markets, farm stands, and produce-focused groceries
is pending verified source data. Convenience stores such as 7-Eleven are outside
the stated qualifying-source policy. Verify actual availability and recurring
hours with providers; a listing or SNAP authorization alone is insufficient.

`data/served_schools.csv` is a sanitized school-ID service crosswalk from the
SY26–27 sheet supplied October 14. Staff contacts and internal notes were omitted
from that crosswalk. The separately supplied original reference workbook is
available unchanged at `data/SBD_Expansion_Model_Final-draft_026.xlsx`; the app
does not automatically import changes from it.

## Maps and spacing

Distances are straight-line miles (Haversine radius 3958.7613 miles), not driving
routes, travel times, or service areas. The confirmed dispatch address is 2901 W.
Hunting Park Avenue, Philadelphia. The default Share coordinates are explicitly
approximate and editable for the session; changing the address label does not
move the pin. Map tiles require browser internet access.

The optional minimum-spacing tool considers only the filtered top 25. In rubric
priority order, it retains each school only if it is strictly farther than the
entered distance from every school already kept. It does not backfill beyond the
current group or guarantee maximum school count/total score. Invalid coordinates
are withheld for review. Decisions, conflict reasons, and weighted pair-by-pair
rubric comparisons are downloadable. School hovers show names only.

## Budgets and outcome records

Planning assumes equal cost per school per cycle and common participation. It
does not model school-specific costs or routing constraints. Comparison/portfolio
exports include planning assumptions, snapshot, and normalized scenario weights.

Outcome records contain aggregate cost, unique students served per school, and
paired food-insecurity survey counts. Blank cells remain missing. Cost per student
uses complete cost/service records; before–after change uses complete paired
survey records. Such changes do not establish causation. Entries persist only
in the session: download the CSV to retain them and upload to resume. No student
names are required. A credible comparison group or randomized phased rollout
would support stronger future evaluation.

## Presentation and accessibility

Each page uses distinct generated decorative artwork matched to its purpose,
served locally as cacheable image files. It does not depict actual service or
constitute source evidence. Faint backgrounds, opaque text/data surfaces, and
raised tables preserve readability. Desktop scrolling gently moves the background;
mobile and reduced-motion settings disable the animated enhancement.

## Validation and deployment

```bash
python -m unittest discover -s tests
```

The tests cover filters, blank defaults, ranking/service consistency, allocation,
outcome validation, spacing feasibility, export context, and page rendering.
Browser checks additionally cover responsive layouts, table scrolling, and static
artwork delivery. For Streamlit Community Cloud, deploy branch `main` with entry
point `app.py`; changes pushed to that branch should trigger an update. If a stale
menu persists, check the deployed branch and reboot from the Streamlit dashboard.
