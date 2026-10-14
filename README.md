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
