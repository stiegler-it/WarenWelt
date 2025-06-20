from decimal import Decimal
from datetime import date
from app.services.rental_invoice_service import calculate_pro_rata_amount

def test_calculate_pro_rata_full_month():
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("100.00"),
        contract_period_start_for_month=date(2024, 7, 1),
        contract_period_end_for_month=date(2024, 7, 31),
        actual_month_start=date(2024, 7, 1),
        actual_month_end=date(2024, 7, 31)
    )
    assert amount == Decimal("100.00")

def test_calculate_pro_rata_partial_month_start():
    # Contract starts mid-month (16th July), month has 31 days. 16 days of rent.
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("310.00"), # 10 EUR per day
        contract_period_start_for_month=date(2024, 7, 16),
        contract_period_end_for_month=date(2024, 7, 31),
        actual_month_start=date(2024, 7, 1),
        actual_month_end=date(2024, 7, 31)
    )
    assert amount == Decimal("160.00") # 16 days * 10 EUR/day

def test_calculate_pro_rata_partial_month_end():
    # Contract ends mid-month (15th July), month has 31 days. 15 days of rent.
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("310.00"),
        contract_period_start_for_month=date(2024, 7, 1),
        contract_period_end_for_month=date(2024, 7, 15),
        actual_month_start=date(2024, 7, 1),
        actual_month_end=date(2024, 7, 31)
    )
    assert amount == Decimal("150.00")

def test_calculate_pro_rata_mid_month_to_mid_month():
    # Contract from 10th July to 20th July. 11 days of rent.
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("310.00"), # 10 EUR per day
        contract_period_start_for_month=date(2024, 7, 10),
        contract_period_end_for_month=date(2024, 7, 20),
        actual_month_start=date(2024, 7, 1),
        actual_month_end=date(2024, 7, 31)
    )
    assert amount == Decimal("110.00")

def test_calculate_pro_rata_february_leap_year():
    # Contract for full February in a leap year (29 days)
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("290.00"), # 10 EUR per day
        contract_period_start_for_month=date(2024, 2, 1),
        contract_period_end_for_month=date(2024, 2, 29),
        actual_month_start=date(2024, 2, 1),
        actual_month_end=date(2024, 2, 29)
    )
    assert amount == Decimal("290.00")

def test_calculate_pro_rata_february_partial_leap_year():
    # Contract for 1st to 10th Feb in a leap year (10 days)
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("290.00"), # 10 EUR per day
        contract_period_start_for_month=date(2024, 2, 1),
        contract_period_end_for_month=date(2024, 2, 10),
        actual_month_start=date(2024, 2, 1),
        actual_month_end=date(2024, 2, 29)
    )
    assert amount == Decimal("100.00")

def test_calculate_pro_rata_zero_days():
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("300.00"),
        contract_period_start_for_month=date(2024, 7, 10),
        contract_period_end_for_month=date(2024, 7, 9), # Ends before it starts
        actual_month_start=date(2024, 7, 1),
        actual_month_end=date(2024, 7, 31)
    )
    assert amount == Decimal("0.00")

def test_calculate_pro_rata_zero_full_amount():
    amount = calculate_pro_rata_amount(
        full_month_amount=Decimal("0.00"),
        contract_period_start_for_month=date(2024, 7, 1),
        contract_period_end_for_month=date(2024, 7, 15),
        actual_month_start=date(2024, 7, 1),
        actual_month_end=date(2024, 7, 31)
    )
    assert amount == Decimal("0.00")
