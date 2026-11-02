import unittest
from names import normalize_name


class NamesTests(unittest.TestCase):
    def test_existing_contract(self):
        self.assertEqual(normalize_name("  Ada  "), "Ada")

    def test_existing_nonstring_rejection(self):
        with self.assertRaises((AttributeError, TypeError)):
            normalize_name(None)
