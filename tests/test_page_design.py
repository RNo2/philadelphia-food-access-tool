from pathlib import Path
import hashlib
import unittest
from page_design import PAGE_ART, artwork_url


class PageDesignTests(unittest.TestCase):
    def test_every_page_has_a_distinct_local_artwork(self):
        root = Path(__file__).resolve().parents[1]
        digests = []
        for name in PAGE_ART.values():
            image = root / 'static' / f'page-{name}.png'
            self.assertTrue(image.is_file(), str(image))
            content = image.read_bytes()
            self.assertTrue(content.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(artwork_url(name), f"app/static/page-{name}.png")
            digests.append(hashlib.sha256(content).hexdigest())
        self.assertEqual(len(set(digests)), len(PAGE_ART))
