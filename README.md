# Philadelphia School Food Access Priority Tool

A public-facing Streamlit decision-support app built from `SBD_Expansion_Model.xlsx`.

## What it includes

- Top-priority school ranking
- Interactive Philadelphia map
- Scenario-weight sliders that recalculate the ranking on an 85-point scale
- Outreach-capacity / portfolio view
- School-level evidence profiles
- Transparent rubric, source links, and limitations

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Put it online for anyone to use

The simplest route is Streamlit Community Cloud:

1. Create a GitHub repository and upload the contents of this folder.
2. In Streamlit Community Cloud, choose **Create app**.
3. Select the repository and set the entry point to `app.py`.
4. Deploy. You will receive a public URL you can share.

No database or API key is required for this version.

## Data refresh

The app reads `data/schools.csv`, which was extracted from the hidden school-level calculation table in the supplied workbook snapshot dated **2026-10-09**. The original workbook is retained at `data/SBD_Expansion_Model.xlsx` for auditability.

When the source workbook is refreshed, regenerate `schools.csv` from the `Data` sheet calculation table (header row beginning with `School ID`, `School`, `Type`, `Level`, `ZIP`, ... near Excel row 2050). For an operational deployment, automate this extraction as part of the organization's refresh process.

## Model interpretation

The baseline scoring rubric totals 85 points:

- Economic need: 30
- Fresh-food access: 25
- Existing food-access resource gap: 25
- Potential reach / enrollment: 5

Scenario controls adjust the *relative* importance of these components and normalize the selected values back to an 85-point total, keeping priority tiers comparable.

## Use note

This is a screening and allocation-support tool, not an automatic eligibility system. Food-access indicators should be field-verified before program commitments.

## Budget & Allocation Lab

Compare need-first, student-reach-first, and economically disadvantaged enrollment
allocations using a budget, equal cost per school per cycle, a school capacity limit,
and a common assumed student participation rate. Need-first follows the sidebar's
scenario weights. Under the equal-cost/common-participation assumptions, selecting
schools with the largest enrollment maximizes estimated participating students.
Costs and participation defaults are illustrative, not measured program inputs.
The model does not include school-specific costs, travel constraints, or causal
benefit estimates. Exported allocations include the planning assumptions.

The lab also offers an aggregate outcome CSV for one evaluation cycle. Track actual
cost, unique students served at each school, and food insecurity before/after among
the same paired survey respondents. Outcome entries are session-only: download to
retain them, and upload the CSV to resume. No student-level data is required or
stored in the repository. Actual cost per student uses schools with complete cost
and service data; before/after change uses complete paired-survey data. Such changes
are descriptive and do not establish causal impact. A comparison group or randomized
phased rollout can support stronger future evaluation.

Run the functional and allocation tests from the repository directory:

```bash
python -m unittest discover -s tests
```

## Served Schools

The Served Schools page uses a sanitized school-ID crosswalk from the supplied
SY26–27 master sheet: 15 current schools and 3 schools below “No longer serving.”
Names were matched against the model's school names and addresses, with abbreviated
names resolved explicitly. Staff contacts, internal notes, and the raw source sheet
are not published. The page shows ranks against the existing eligible-school scenario
pool, including listed served schools; it does not change existing allocation
candidates. Scores respond to sidebar weights, and former service is displayed
separately. Enrollment and economic-need values remain from the model snapshot.

## Workbook columns and nearby food-site evidence

The overview, school directory, served-school tables, and portfolio views include
food-evidence status, the reason a school needs attention, and its source Staff
Review row, alongside food-distance/resource counts. The overview and directory
also expose sequential scenario order separately from the shared-score rank.

`data/food_sites.csv` contains the 309 public food-site listings extracted from the
Data sheet (row 510 header) of `SBD_Expansion_Model_10.20.2026.xlsx`, supplied October
20, 2026. The workbook reports government source retrieval on October 9, 2026.
Workbook profile-distance/order columns were intentionally omitted because they
apply only to the workbook's selected school. School Explorer and Food Resources
recompute straight-line Haversine distances per selected school (earth radius
3958.7613 miles), showing active candidate Food Sites within one mile and excluding
recorded closures. Provider websites and the original City dataset reference are
clickable. These are saved listings, not freshly verified opening hours, service
eligibility, or available food. Counts can differ from the school's distinct-address
resource metric when multiple listings share an address. No raw Staff Review notes
or contact records were imported.

## Top 20 Staff Map

A separate staff planning page keeps the original Priority Map and Top 15 overview
unchanged. It selects the top 20 within the chosen school types and grade levels under
current scenario weights. Filters apply before the 20-school limit; fewer schools
appear only when fewer than 20 eligible, unserved schools match. Ties retain the existing deterministic order. Labels show
scenario order while tables retain shared-score rank.

Staff can view Share-to-school connections, flag nearby school pairs using an
adjustable threshold, compare any two schools, inspect the full distance grid,
sort by distance from Share, and download school and pair-distance CSVs. A blank Served Schools filter includes both currently served schools from the
supplied crosswalk and schools not listed as currently served. Selecting either
group applies that restriction before the top-20 limit, distance comparisons,
and exports. Other pages retain their existing candidate pools. School hover labels show only
the school name.

The confirmed dispatch address is 2901 W. Hunting Park Avenue, Philadelphia, PA
19129. Live geocoding was blocked during development; the initial Share coordinates
are explicitly approximate and can be edited for the current session. The address
label alone does not geocode or move the pin. Exports include the entered hub label
and coordinates. All distances are straight-line Haversine miles, not driving miles,
travel times, service catchments, or evidence of duplicated benefits. Invalid school
coordinates are flagged and excluded only from geographic calculations. Map tiles
require browser internet access. This page has no access restriction; it is part of
the existing public app.

## Blank input defaults

All input/filter boxes start blank in a fresh session. Empty school filters mean
no restriction; selections apply before top-N limits. Blank scenario-weight inputs
use the documented baseline values without pre-populating the boxes. Budget
calculations wait for explicit budget, school cost, capacity, and participation
entries. School profiles and two-school comparisons wait for explicit selections.
Blank location overrides retain the labeled approximate Share pin; blank proximity
thresholds produce no close-pair flags. User-entered choices persist during a session.

## School display counts

Overview defaults to 25 schools after filtering. Its blank school-count control
uses 25 until a user enters another count; the table and enrollment metric update
together. Distance review selects up to 25 after school-type, level, and service
filters. Fewer results appear only when fewer schools match.

## Minimum-spacing recommendations

Distance review has an optional blank `Minimum school separation (miles)` input.
Entering a value compares the currently filtered top 25 and builds a priority-first
shortlist: sort by scenario score, economic-disadvantage rate, enrollment, then
School ID; retain a school only if it is strictly farther than the entered distance
from every school already recommended. Schools with invalid coordinates are held
for review. This greedy rule favors the highest-priority schools; it does not
maximize total score or the number of schools. It does not backfill outside the
current top 25 or infer that proximity proves duplicated beneficiaries.

The map colors recommended schools green and excluded schools gray. Downloadable
decisions identify which recommended schools blocked an exclusion. Pair-by-pair
comparisons show both schools' scores, economic-disadvantage rate, enrollment,
food-access indicators, current weighted rubric contributions, and final statuses.
Two nearby schools may both be excluded if each conflicts with other recommended
schools. Recommendations update with school/service filters, weights, and distance.

## Page artwork and scrolling

Each page has its own locally hosted decorative 3D artwork themed to its purpose.
The imagery is generated illustration, not evidence of actual schools, locations,
service, or financial results. A white overlay and opaque tables/charts preserve
readability. Desktop browsers supporting CSS scroll timelines gently move the
background with the main page scroll. Other browsers use native scrolling
backgrounds. Mobile and reduced-motion settings disable the animated enhancement.
The artwork does not change data, ranks, filters, or input defaults and requires
no external image-hosting service or animation library at runtime.
