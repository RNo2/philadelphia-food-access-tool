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
