from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
from staff_map import miles_between, distance_tables, select_top_schools

ROOT = Path(__file__).resolve().parents[1]


class StaffMapTests(unittest.TestCase):
    def test_distances_and_invalid_coordinates(self):
        self.assertEqual(float(miles_between(40, -75, 40, -75)), 0)
        self.assertAlmostEqual(float(miles_between(0, 0, 0, 1)), 69.0934, places=3)
        schools = pd.DataFrame({'School':['A','B','C'], 'School ID':['1','2','3'], 'Latitude':[40,40.01,None], 'Longitude':[-75,-75,-75]})
        mapped, pairs, matrix = distance_tables(schools, 40, -75)
        self.assertEqual(len(mapped), 2)
        self.assertEqual(len(pairs), 1)
        self.assertAlmostEqual(matrix[0,1], matrix[1,0])
        self.assertEqual(mapped.iloc[0]['Miles from Share (approx.)'], 0)
        self.assertGreater(pairs.iloc[0]['Miles apart'], 0)

    def test_cohort_filter_modes(self):
        schools = pd.DataFrame({'School ID':range(30),'Type':['District']*20+['Charter']*10,'Level':['High']*30})
        self.assertTrue(select_top_schools(schools, ['Charter'], ['High'], 'Filter the overall top 20').empty)
        self.assertEqual(len(select_top_schools(schools, ['Charter'], ['High'], 'Top 20 within selected school types and levels')),10)

    def test_staff_map_controls(self):
        app = AppTest.from_file(str(ROOT/'app.py'), default_timeout=60).run()
        app.sidebar.radio[0].set_value('Top 20 Staff Map').run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len(app.dataframe[0].value),20)
        self.assertTrue((app.dataframe[0].value['Miles from Share (approx.)'] >= 0).all())
        app.multiselect(key='staff_types').set_value(['District']).run()
        self.assertFalse(app.exception)
        self.assertTrue(app.dataframe[0].value['Type'].eq('District').all())
        app.radio(key='staff_scope').set_value('Top 20 within selected school types and levels').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value),20)
        app.slider(key='staff_threshold').set_value(3.0).run()
        self.assertFalse(app.exception)
        self.assertTrue((app.dataframe[1].value['Miles apart']<3).all())
        app.checkbox(key='staff_spokes').set_value(False).run()
        app.checkbox(key='staff_served').set_value(False).run()
        app.selectbox(key='staff_style').set_value('Dark').run()
        self.assertFalse(app.exception)
        app.multiselect(key='staff_types').set_value([]).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertTrue(app.dataframe[0].value.empty)
