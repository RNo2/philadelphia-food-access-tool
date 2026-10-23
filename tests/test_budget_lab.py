from io import StringIO
from pathlib import Path
import unittest
import pandas as pd
from streamlit.testing.v1 import AppTest
from budget_lab import allocate, outcome_template, validate_outcomes


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.schools = pd.DataFrame({"School ID": ["1", "2", "3"], "School": ["A", "B", "C"], "Enrollment": [100, 500, 300], "Economic %": [.9, .2, .8], "Scenario score": [80, 50, 60]})

    def test_constraints_and_objectives(self):
        portfolios, summary = allocate(self.schools, 250, 100, 2, .5)
        self.assertEqual(portfolios['Need first']['School ID'].tolist(), ['1', '3'])
        self.assertEqual(portfolios['Student reach first']['School ID'].tolist(), ['2', '3'])
        self.assertEqual(portfolios['Economic disadvantage first']['School ID'].tolist(), ['3', '2'])
        self.assertTrue((summary['Estimated spend ($)'] <= 250).all())
        self.assertTrue((summary['Unallocated budget ($)'] == 50).all())
        self.assertEqual(summary.set_index('Strategy').loc['Student reach first', 'Estimated participating students'], 400)

    def test_zero_and_capacity(self):
        for budget, capacity in [(0, 2), (99, 2), (1000, 0)]:
            p, s = allocate(self.schools, budget, 100, capacity, 0)
            self.assertTrue(all(x.empty for x in p.values()))
            self.assertTrue((s['Schools'] == 0).all())
        _, s = allocate(self.schools, 1000, 100, 1, 0)
        self.assertTrue((s['Schools'] == 1).all())
        self.assertTrue((s['Estimated participating students'] == 0).all())
        with self.assertRaises(ValueError):
            allocate(self.schools, 100, 0, 1, .5)

    def test_outcomes_validation_and_csv(self):
        log = outcome_template(self.schools.head(1))
        log.loc[0, ['Actual cost ($)', 'Students served', 'Paired survey responses', 'Food insecure before', 'Food insecure after']] = [150, 30, 20, 15, 10]
        actual = validate_outcomes(pd.read_csv(StringIO(log.to_csv(index=False)), dtype={'School ID': str}), self.schools)
        self.assertEqual(actual.loc[0, 'Students served'], 30)
        for column, bad in [('Students served', -1), ('Students served', 1.5), ('Actual cost ($)', float('inf')), ('Food insecure after', 21), ('Paired survey responses', 31)]:
            copy = log.copy(); copy.loc[0, column] = bad
            with self.assertRaises(ValueError):
                validate_outcomes(copy, self.schools)
        with self.assertRaises(ValueError):
            validate_outcomes(pd.concat([log, log]), self.schools)
        copy = log.copy(); copy.loc[0, 'School ID'] = 'unknown'
        with self.assertRaises(ValueError):
            validate_outcomes(copy, self.schools)


class BudgetPageTests(unittest.TestCase):
    def test_lab_renders_and_recalculates(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=60).run()
        app.sidebar.radio[0].set_value('Budget & Allocation Lab').run()
        self.assertFalse(app.exception, [e.message for e in app.exception])
        self.assertEqual(len(app.tabs), 2)
        self.assertTrue(app.dataframe[0].value.empty)
        for key, value in [('lab_budget',25000.0), ('lab_cost',1500.0), ('lab_capacity',15), ('lab_participation',25)]:
            self.assertIsNone(app.number_input(key=key).value)
            app.number_input(key=key).set_value(value).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[0].value['Schools'].tolist(), [15, 15, 15])
        app.number_input(key='lab_budget').set_value(0.0).run()
        self.assertFalse(app.exception)
        self.assertTrue((app.dataframe[0].value['Schools'] == 0).all())
        self.assertTrue(app.warning)
        app.number_input(key='lab_budget').set_value(25000.0).run()
        app.radio(key='lab_strategy').set_value('Student reach first').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[1].value), 15)
        # A new outcome log starts blank: no invented observed benefit.
        [b for b in app.button if b.label == 'Use selected portfolio for a new outcome log'][0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state['lab_outcomes']['Students served'].isna().all())
        self.assertTrue(any(m.value == 'Not available' for m in app.metric))
        log = app.session_state['lab_outcomes'].copy()
        log.loc[0, ['Actual cost ($)', 'Students served', 'Paired survey responses', 'Food insecure before', 'Food insecure after']] = [150, 30, 20, 15, 10]
        app.session_state['lab_outcomes'] = log
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(any(m.value == '$5.00' for m in app.metric))
        self.assertTrue(any(m.value == '25.0 percentage points' for m in app.metric))
        [b for b in app.button if b.label == 'Calculate observed outcomes'][0].click().run()
        self.assertFalse(app.exception)
        [b for b in app.button if b.label == 'Clear session outcome log'][0].click().run()
        self.assertFalse(app.exception)
        self.assertNotIn('lab_outcomes', app.session_state)


if __name__ == '__main__':
    unittest.main()
