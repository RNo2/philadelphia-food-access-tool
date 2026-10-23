from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
from presentation import attach_service_status, review_brief, export_with_context, weighted_components, BASE_WEIGHTS

ROOT = Path(__file__).resolve().parents[1]


class PresentationTests(unittest.TestCase):
    def test_service_crosswalk_preserves_scoring_data(self):
        original = pd.read_csv(ROOT/'data/schools.csv', dtype={'School ID':str})
        service = pd.read_csv(ROOT/'data/served_schools.csv', dtype={'School ID':str})
        enriched = attach_service_status(original,service)
        pd.testing.assert_frame_equal(original,enriched[original.columns])
        self.assertEqual(enriched['Service status'].value_counts()['Currently served'],15)
        self.assertEqual(enriched['Service status'].value_counts()['Formerly served'],3)
        enriched.loc[0,'Already served']='Yes'
        self.assertEqual(attach_service_status(enriched,service).iloc[0]['Service status'],'Currently served')

    def test_export_context_and_contributions(self):
        school = pd.Series({'School ID':'1','School':'Example | School','Type':'District','Level':'High', 'Scenario rank':1,'Scenario score':70.,'Service status':'Currently served', 'Economic points':25,'Fresh points':20,'Resource points':20,'Reach points':5})
        components = weighted_components(school,BASE_WEIGHTS)
        self.assertEqual(components['Scenario contribution'].sum(),70)
        brief = review_brief(pd.DataFrame([school]),BASE_WEIGHTS,'October 9, 2026',{'Types':['District']}).decode()
        self.assertIn('Example / School',brief)
        self.assertIn('District',brief)
        self.assertIn('Currently served',brief)
        self.assertIn('October 9, 2026',export_with_context(pd.DataFrame([school]),BASE_WEIGHTS,'October 9, 2026').decode())

    def test_overview_service_filter_and_clear(self):
        app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
        app.multiselect(key='overview_service').set_value(['Currently served']).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len(app.dataframe[0].value),15)
        self.assertTrue(app.dataframe[0].value['Service status'].eq('Currently served').all())
        app.button(key='overview_clear').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.multiselect(key='overview_service').value,[])
        self.assertEqual(len(app.dataframe[0].value),25)

    def test_empty_scenario_and_literal_search(self):
        app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
        app.sidebar.radio[0].set_value('Scenario Lab').run()
        self.assertFalse(app.exception)
        self.assertFalse(any('nan' in m.value.lower() for m in app.metric))
        app.sidebar.radio[0].set_value('School Explorer').run()
        app.text_input[0].set_value('[').run()
        self.assertFalse(app.exception)
        self.assertTrue(app.warning)

    def test_navigation_and_baseline_reset(self):
        app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
        app.sidebar.number_input(key='weight_e').set_value(60).run()
        app.sidebar.button(key='restore_weights').click().run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.sidebar.number_input(key='weight_e').value)
        [b for b in app.button if b.label=='2 · Review distance and spacing'][0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.sidebar.radio[0].value,'Distance review')

    def test_outcomes_accessible_without_budget_plan(self):
        app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
        app.sidebar.radio[0].set_value('Budget & Allocation Lab').run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.number_input(key='lab_budget').value)
        self.assertTrue(any('outcome CSV' in uploader.label for uploader in app.get('file_uploader')))
        app.multiselect(key='lab_service').set_value(['Currently served']).run()
        self.assertFalse(app.exception)
        self.assertTrue(any('15 matching candidates' in caption.value for caption in app.caption))
