from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
from presentation import expansion_candidates
from budget_lab import allocate
from staff_map import select_top_schools, spacing_recommendation

ROOT = Path(__file__).resolve().parents[1]


class ServiceExclusionTests(unittest.TestCase):
    def test_defensive_exclusion_before_selection_and_allocation(self):
        schools = pd.DataFrame({'School ID':['1','2','3','4'], 'School':['Current','Former','Unchecked','Flagged'],
            'Service status':['Currently served',' Formerly served ','Not listed as served','Not listed as served'],
            'Already served':['No','No','No',' Yes '], 'Scenario score':[85,84,20,83],
            'Economic %':[.9]*4,'Enrollment':[100]*4,'Type':['District']*4,'Level':['High']*4,
            'Latitude':[40,40.1,40.2,40.3],'Longitude':[-75]*4})
        self.assertEqual(expansion_candidates(schools)['School ID'].tolist(),['3'])
        self.assertEqual(select_top_schools(schools,[],[])['School ID'].tolist(),['3'])
        portfolios,_ = allocate(schools,1000,100,10,.5)
        for portfolio in portfolios.values():
            self.assertEqual(portfolio['School ID'].tolist(),['3'])
        self.assertEqual(spacing_recommendation(schools,1)['School ID'].tolist(),['3'])

    def test_all_recommendation_pages_exclude_service_history(self):
        service = pd.read_csv(ROOT/'data/served_schools.csv',dtype={'School ID':str})
        blocked_ids = set(service['School ID'])
        schools = pd.read_csv(ROOT/'data/schools.csv',dtype={'School ID':str})
        blocked_names = set(schools.loc[schools['School ID'].isin(blocked_ids),'School'])
        app = AppTest.from_file(str(ROOT/'app.py'),default_timeout=60).run()
        overview = app.dataframe[0].value['School'].tolist()
        self.assertTrue(set(overview).isdisjoint(blocked_names))
        app.sidebar.radio[0].set_value('Distance review').run()
        self.assertEqual(app.dataframe[0].value['School'].tolist(),overview)
        for page in ['All Rankable Schools','Priority Map']:
            app.sidebar.radio[0].set_value(page).run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            table=app.dataframe[0].value
            self.assertEqual(len(table),275)
            self.assertTrue(set(table['School ID']).isdisjoint(blocked_ids))
        app.sidebar.radio[0].set_value('Scenario Lab').run()
        next(n for n in app.number_input if n.label=='Outreach capacity this cycle (schools)').set_value(50).run()
        portfolio=next(d.value for d in app.dataframe if 'Scenario score' in d.value.columns)
        self.assertTrue(set(portfolio['School']).isdisjoint(blocked_names))
        self.assertTrue(any('No rank changes' in info.value for info in app.info))
        app.sidebar.radio[0].set_value('Budget & Allocation Lab').run()
        for key,value in [('lab_budget',1000000.0),('lab_cost',1.0),('lab_capacity',275),('lab_participation',25)]:
            app.number_input(key=key).set_value(value).run()
        app.radio(key='lab_strategy').set_value('Need first').run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        portfolio=next(d.value for d in app.dataframe if 'Estimated school cost ($)' in d.value.columns)
        self.assertEqual(len(portfolio),275)
        self.assertTrue(set(portfolio['School ID']).isdisjoint(blocked_ids))
