from somweb.core import DoorStatus
from typing import Type
import unittest
import requests_mock
from somweb import Door, DoorStatusType, SomwebClient as Client

class TestSomwebClient(unittest.TestCase):
    """
    Test as a playground
    """

    def test_quickly(self):
        d = Door(3, "Jadda")
        s = f"[{d.id}] {d.name}"
        self.assertEqual("[3] Jadda", s)

if __name__ == "__main__":
    unittest.main()
