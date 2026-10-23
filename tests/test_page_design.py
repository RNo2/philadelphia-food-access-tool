from pathlib import Path
import hashlib
import unittest
from page_design import PAGE_ART, artwork_data


class PageDesignTests(unittest.TestCase):
    def test_every_page_has_a_distinct_local_artwork(self):
        root = Path(__file__).resolve().parents[1]
        digests = []
        for name in PAGE_ART.values():
            image = root / 'assets' / f'page-{name}.png'
            self.assertTrue(image.is_file(), str(image))
            content = image.read_bytes()
            self.assertTrue(content.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertTrue(artwork_data(name))
            digests.append(hashlib.sha256(content).hexdigest())
        self.assertEqual(len(set(digests)), len(PAGE_ART))
