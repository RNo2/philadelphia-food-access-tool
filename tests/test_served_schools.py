from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class ServedSchoolTests(unittest.TestCase):
    def test_source_status_matching_and_public_fields(self):
        source = pd.read_csv(ROOT / 'data/served_schools.csv', dtype={'School ID': str})
        self.assertEqual(source['Service status'].value_counts().to_dict(), {'Currently served': 15, 'Formerly served': 3})
        self.assertFalse(source['School ID'].duplicated().any())
        self.assertEqual(set(source.columns), {'School ID', 'Source school name', 'Service status', 'Match basis'})
        schools = pd.read_csv(ROOT / 'data/schools.csv', dtype={'School ID': str})
        self.assertTrue(source['School ID'].isin(schools['School ID']).all())

    def test_ranks_filters_and_scenarios(self):
        app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
        app.sidebar.radio[0].set_value('All Rankable Schools').run()
        reference = app.dataframe[0].value.set_index('School ID')
        app.sidebar.radio[0].set_value('Served Schools').run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        table = app.dataframe[0].value
        self.assertEqual(len(table), 15)
        for _, row in table.iterrows():
            self.assertEqual(row['Scenario rank'], reference.loc[row['School ID'], 'Scenario rank'])
        kelly = table.set_index('School ID').loc['6470']
        self.assertEqual(kelly['Score /85'], 42)
        self.assertEqual(kelly['School level'], 'Elementary')
        app.sidebar.slider[0].set_value(60).run()
        self.assertFalse(app.exception)
        self.assertNotEqual(table['Score /85'].tolist(), app.dataframe[0].value['Score /85'].tolist())
        app.radio[0].set_value('Formerly served').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value), 3)
        app.radio[0].set_value('All listed schools').run()
        self.assertEqual(len(app.dataframe[0].value), 18)
        app.text_input[0].set_value('not-a-school').run()
        self.assertFalse(app.exception)
        self.assertTrue(app.dataframe[0].value.empty)
