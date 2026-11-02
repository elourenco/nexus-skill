import unittest
from names import normalize_name

class NamesTests(unittest.TestCase):
    def test_strips_surrounding_space(self):
        self.assertEqual(normalize_name("  Ada  "), "Ada")
    def test_preserves_internal_space(self):
        self.assertEqual(normalize_name("Ada  Lovelace"), "Ada  Lovelace")
    def test_rejects_non_string(self):
        with self.assertRaises((AttributeError, TypeError)):
            normalize_name(None)
