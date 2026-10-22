from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class BlankInputTests(unittest.TestCase):
    def test_all_pages_start_with_blank_input_controls(self):
        path = Path(__file__).resolve().parents[1] / 'app.py'
        pages = ['Overview', 'All Rankable Schools', 'Served Schools', 'Food Resources',
                 'Priority Map', 'Distance review', 'Budget & Allocation Lab',
                 'Scenario Lab', 'School Explorer']
        for page in pages:
            with self.subTest(page=page):
                app = AppTest.from_file(str(path), default_timeout=60).run()
                app.sidebar.radio[0].set_value(page).run()
                self.assertFalse(app.exception, [e.message for e in app.exception])
                for widget in app.multiselect:
                    self.assertEqual(widget.value, [])
                for widget in app.selectbox:
                    self.assertIsNone(widget.value)
                for widget in app.number_input:
                    self.assertIsNone(widget.value)
                for widget in app.text_input:
                    self.assertEqual(widget.value, '')
                for widget in app.checkbox:
                    self.assertFalse(widget.value)
                self.assertEqual(app.sidebar.number_input[0].value, None)
