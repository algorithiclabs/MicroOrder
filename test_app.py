import unittest

from app import amount_to_cents, valid_email


class ValidationTest(unittest.TestCase):
    def test_amount_conversion(self):
        self.assertEqual(amount_to_cents("350.00"), 35000)

    def test_invalid_amount_rejected(self):
        with self.assertRaises(ValueError):
            amount_to_cents("0")

    def test_email_validation(self):
        self.assertTrue(valid_email("person@example.com"))
        self.assertFalse(valid_email("not-an-email"))


if __name__ == "__main__":
    unittest.main()
