from datetime import datetime
from datetime import timedelta

from payment import Payment


class TestPayment:
    def test_paid_status(self):
        pmt: Payment = Payment()
        assert not pmt.paid
        assert pmt.paid_status == "not yet paid"
        pmt.paid = True
        assert pmt.paid
        assert pmt.paid_status == "paid"

    def test_payable_within_2days(self):
        pmt: Payment = Payment(due_date=datetime.now())
        assert pmt.payable_within_2days
        pmt.paid = True
        assert not pmt.payable_within_2days

        pmt.paid = False
        pmt.due_date += timedelta(days=3)
        assert not pmt.payable_within_2days
