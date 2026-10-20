from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
from food_evidence import load_food_sites, nearby_food_sites

ROOT = Path(__file__).resolve().parents[1]


class FoodEvidenceTests(unittest.TestCase):
    def test_workbook_profile_matches_bartram(self):
        sites = load_food_sites()
        nearby = nearby_food_sites(sites, 39.92149737, -75.23405562)
        self.assertEqual(nearby['Site name'].tolist(), [
            'Revelation Philadelphia Ministry Inc',
            'Catholic Social Services Southwest Family Service Center',
            'Resurrection Community Church',
            'Ezekiel Baptist Church',
        ])
        self.assertAlmostEqual(nearby.iloc[0]['Miles'], 0.19201505426076063, places=6)
        self.assertEqual(nearby.iloc[3]['Website'], 'https://www.philabundance.org/')
        self.assertTrue((nearby['Status'] == 'Active').all())
        self.assertTrue(nearby['Source URL'].str.startswith('https://services.arcgis.com/').all())
        self.assertEqual(len(sites), 309)

    def test_closures_distance_and_missing_coordinates(self):
        sites = load_food_sites()
        self.assertTrue(nearby_food_sites(sites, float('nan'), -75).empty)
        self.assertTrue(nearby_food_sites(sites, 91, -75).empty)
        self.assertTrue(nearby_food_sites(sites, 0, 0).empty)
        active = sites[sites['Candidate'].eq('Yes')].iloc[0]
        candidates = pd.DataFrame([active.copy() for _ in range(3)]).astype(object)
        candidates.iloc[1, candidates.columns.get_loc('Temporary closure')] = 'yes'
        candidates.iloc[2, candidates.columns.get_loc('Status')] = 'Permanently Closed'
        result = nearby_food_sites(candidates, active['Latitude'], active['Longitude'])
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.iloc[0]['Miles'], 0)

    def test_tables_and_school_profile(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
        for name in ['Overview', 'All Rankable Schools', 'Served Schools']:
            app.sidebar.radio[0].set_value(name).run()
            self.assertFalse(app.exception, [e.message for e in app.exception])
            self.assertTrue({'Food evidence', 'Why it needs attention', 'Review row'}.issubset(app.dataframe[0].value.columns))
        app.sidebar.radio[0].set_value('School Explorer').run()
        app.selectbox[0].set_value('John Bartram High School').run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len(app.dataframe[0].value), 4)
        self.assertTrue({'Food site', 'Miles', 'Address', 'Website', 'Source URL'}.issubset(app.dataframe[0].value.columns))
        app.sidebar.radio[0].set_value('Food Resources').run()
        app.selectbox[0].set_value('1010').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[1].value), 4)
