import pytest
from ledgerline.fees.schedule import calculate_fee, STANDARD
from ledgerline.core.money import Money

def test_calculate_fee_large_payment_uses_tiered_schedule():
    # $50,000.00 payment should be charged according to the tiered schedule:
    # 1,000 @ 2.9% = $29.00
    # 9,000 @ 2.4% = $216.00
    # 40,000 @ 1.8% = $720.00
    # flat fee = $0.30
    # Total expected fee = $965.30
    amount = Money.from_major("50000.00", "USD")
    fee = calculate_fee(amount, STANDARD)

    # Expected fee in minor units (cents)
    expected_minor = 96530  # $965.30 -> 96,530 cents
    assert fee.minor == expected_minor, f"Expected fee minor {expected_minor}, got {fee.minor}"
    assert fee.currency == "USD"
