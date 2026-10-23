from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from staff_map import spacing_recommendation, miles_between


class SpacingTests(unittest.TestCase):
    def sample(self):
        return pd.DataFrame({'School ID':['1','2','3','4'], 'School':['A','B','C','Missing'],
                             'Scenario score':[80,70,60,90], 'Economic %':[.8,.9,.7,.8], 'Enrollment':[100,200,300,100],
                             'Latitude':[40,40.01,40.02,np.nan], 'Longitude':[-75,-75,-75,-75]})

    def test_chain_and_missing_coordinates(self):
        result = spacing_recommendation(self.sample(), 1)
        decision = result.set_index('School')['Decision']
        self.assertEqual(decision['A'], 'Recommend')
        self.assertEqual(decision['B'], 'Leave out')
        self.assertEqual(decision['C'], 'Recommend')
        self.assertEqual(decision['Missing'], 'Needs coordinate review')
        kept = result[result['Decision'].eq('Recommend')]
        self.assertGreater(float(miles_between(*kept.iloc[0][['Latitude','Longitude']], *kept.iloc[1][['Latitude','Longitude']])), 1)

    def test_tie_break_and_boundary(self):
        sample = self.sample().head(2).copy()
        sample['Scenario score'] = 70
        result = spacing_recommendation(sample, 1)
        self.assertEqual(result[result['Decision'].eq('Recommend')]['School'].tolist(), ['B'])
        threshold = float(miles_between(40,-75,40.01,-75))
        result = spacing_recommendation(sample, threshold)
        self.assertEqual(int(result['Decision'].eq('Recommend').sum()), 1)
        with self.assertRaises(ValueError):
            spacing_recommendation(sample, -1)

    def test_page_recommendations_and_rubric(self):
        root = Path(__file__).resolve().parents[1]
        app = AppTest.from_file(str(root/'app.py'),default_timeout=60).run()
        app.sidebar.radio[0].set_value('Distance review').run()
        self.assertIsNone(app.number_input(key='staff_spacing').value)
        app.number_input(key='staff_spacing').set_value(1.0).run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        decisions = next(d.value for d in app.dataframe if 'Decision' in d.value.columns)
        self.assertEqual(len(decisions),25)
        schools = pd.read_csv(root/'data/schools.csv',dtype={'School ID':str}).set_index('School ID')
        ids = decisions.loc[decisions.Decision.eq('Recommend'),'School ID'].tolist()
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                self.assertGreater(float(miles_between(schools.loc[a,'Latitude'],schools.loc[a,'Longitude'],schools.loc[b,'Latitude'],schools.loc[b,'Longitude'])),1)
        comparison = next(d.value for d in app.dataframe if 'A: Scenario score' in d.value.columns)
        for side in ['A','B']:
            contributions = comparison[[f'{side}: {c}' for c in ['Economic contribution','Fresh-access contribution','Resource-gap contribution','Reach contribution']]].sum(axis=1)
            self.assertTrue(np.allclose(contributions, comparison[f'{side}: Scenario score']))
        app.sidebar.number_input(key='weight_e').set_value(60).run()
        self.assertFalse(app.exception)
        app.number_input(key='staff_spacing').set_value(50.0).run()
        self.assertFalse(app.exception)
        decisions = next(d.value for d in app.dataframe if 'Decision' in d.value.columns)
        self.assertEqual(int(decisions.Decision.eq('Recommend').sum()),1)
