from __future__ import annotations

import unittest

from citywheels.tools import calculate_refund, get_booking, search_policies


class PolicyToolTests(unittest.TestCase):
    def test_finds_opening_hours(self) -> None:
        result = search_policies("What time do you open on Saturday?")
        text = " ".join(match["text"] for match in result["matches"])
        self.assertTrue(result["found"])
        self.assertIn("08:00", text)
        self.assertIn("20:00", text)

    def test_returns_no_match_for_unsupported_topic(self) -> None:
        result = search_policies("Do you offer airport pickup?")
        self.assertFalse(result["found"])


class BookingToolTests(unittest.TestCase):
    def test_get_booking_is_case_insensitive(self) -> None:
        result = get_booking("cw-1001")
        self.assertTrue(result["found"])
        self.assertEqual("CW-1001", result["booking"]["id"])

    def test_unknown_booking_is_a_clear_result(self) -> None:
        result = get_booking("CW-9999")
        self.assertFalse(result["found"])
        self.assertIn("not found", result["message"].lower())


class RefundToolTests(unittest.TestCase):
    def test_48_hours_or_more_refunds_all_rent_and_deposit(self) -> None:
        result = calculate_refund("CW-1001")
        self.assertEqual(100, result["rental_refund_percentage"])
        self.assertEqual(40.0, result["rental_refund_eur"])
        self.assertEqual(50.0, result["deposit_refund_eur"])
        self.assertEqual(90.0, result["total_refund_eur"])

    def test_24_to_48_hours_refunds_half_rent_and_deposit(self) -> None:
        result = calculate_refund("CW-1002")
        self.assertEqual(50, result["rental_refund_percentage"])
        self.assertEqual(40.0, result["rental_refund_eur"])
        self.assertEqual(300.0, result["deposit_refund_eur"])
        self.assertEqual(0.0, result["booking_fee_refund_eur"])
        self.assertEqual(340.0, result["total_refund_eur"])

    def test_less_than_24_hours_refunds_only_deposit(self) -> None:
        result = calculate_refund("CW-1003")
        self.assertEqual(0, result["rental_refund_percentage"])
        self.assertEqual(0.0, result["rental_refund_eur"])
        self.assertEqual(50.0, result["deposit_refund_eur"])
        self.assertEqual(50.0, result["total_refund_eur"])

    def test_non_confirmed_booking_is_not_refundable(self) -> None:
        for booking_id in ("CW-1005", "CW-1006", "CW-1008"):
            with self.subTest(booking_id=booking_id):
                result = calculate_refund(booking_id)
                self.assertFalse(result["eligible"])
                self.assertEqual(0.0, result["total_refund_eur"])

    def test_voucher_refund_is_not_cash(self) -> None:
        result = calculate_refund("CW-1004")
        self.assertEqual(73.0, result["total_refund_eur"])
        self.assertEqual("new voucher", result["refund_method"])
        self.assertIn("voucher", result["message"].lower())

    def test_unknown_booking_has_zero_refund_and_does_not_raise(self) -> None:
        result = calculate_refund("CW-9999")
        self.assertFalse(result["found"])
        self.assertEqual(0.0, result["total_refund_eur"])


if __name__ == "__main__":
    unittest.main()