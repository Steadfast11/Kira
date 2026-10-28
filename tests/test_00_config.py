# Astra project — Copyright (c) 2026 Xasan Abdukhafizov.
"""Discovery with -s tests imports modules directly; initialize scratch config first."""
from tests import config
import kira
import unittest


class ConfigTests(unittest.TestCase):
    def test_import_uses_scratch_config(self):
        self.assertEqual(kira.DIR, config.name)
