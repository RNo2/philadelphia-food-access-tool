from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(APP), default_timeout=60).run()
        self.assert_ok()

    def assert_ok(self):
        self.assertFalse(self.app.exception, [e.message for e in self.app.exception])

    def page(self, name):
        self.app.sidebar.radio[0].set_value(name).run()
        self.assert_ok()

    def test_overview_filters_before_top15(self):
        self.app.multiselect(key='overview_types').set_value(['District']).run()
        self.assert_ok()
        table = self.app.dataframe[0].value
        self.assertEqual(len(table), 15)
        self.assertTrue(table['Type'].eq('District').all())
        self.app.multiselect(key='overview_levels').set_value(['Elementary']).run()
        self.assert_ok()
        table = self.app.dataframe[0].value
        self.assertEqual(len(table), 15)
        self.assertTrue(table['School level'].eq('Elementary').all())
        self.assertEqual(int(self.app.metric[3].value.replace(',', '')), int(table['Enrollment'].sum()))
        self.app.multiselect(key='overview_types').set_value([]).run()
        self.assert_ok()
        self.assertTrue(self.app.dataframe[0].value.empty)
        self.assertEqual(self.app.metric[1].value, '0')

    def test_directory_filters_and_scenario(self):
        self.page("All Rankable Schools")
        table = self.app.dataframe[0].value
        self.assertEqual(len(table), 293)
        self.assertTrue({"School type", "School level"}.issubset(table.columns))
        scores = table["Score /85"].tolist()
        self.app.sidebar.slider[0].set_value(60).run()
        self.assert_ok()
        self.assertNotEqual(scores, self.app.dataframe[0].value["Score /85"].tolist())
        self.app.multiselect[1].set_value(["High"]).run()
        self.assert_ok()
        self.assertEqual(set(self.app.dataframe[0].value["School level"]), {"High"})
        self.app.text_input[0].set_value("[").run()
        self.assert_ok()
        self.assertTrue(self.app.dataframe[0].value.empty)

    def test_food_resources(self):
        self.page("Food Resources")
        buttons = self.app.get("link_button")
        self.assertEqual(len(buttons), 3)
        self.assertTrue(any("have not been verified" in info.value for info in self.app.info))
        self.assertEqual(len(self.app.dataframe[0].value), 293)
        self.assertIn("Food evidence", self.app.dataframe[0].value.columns)
        self.app.multiselect[0].set_value([]).run()
        self.assert_ok()
        self.assertTrue(self.app.warning)

    def test_map_controls(self):
        self.page("Priority Map")
        school_id = self.app.dataframe[0].value.iloc[0]["School ID"]
        self.app.selectbox[0].set_value(school_id).run()
        self.assert_ok()
        self.app.checkbox[0].set_value(True).run()
        self.assert_ok()
        for style in ["Dark", "Street"]:
            self.app.selectbox[1].set_value(style).run()
            self.assert_ok()
        self.app.multiselect[0].set_value([]).run()
        self.assert_ok()
        self.assertTrue(self.app.dataframe[0].value.empty)
        self.assertTrue(self.app.warning)

    def test_existing_pages(self):
        self.assertEqual(len(self.app.dataframe[0].value), 15)
        for name in ["Scenario Lab", "School Explorer", "Methodology & Sources", "Analytical Framework"]:
            self.page(name)


if __name__ == "__main__":
    unittest.main()
