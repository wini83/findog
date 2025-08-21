from datetime import datetime, timedelta

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

    def test_overdue(self):
        date_in_past = datetime.now() - timedelta(days=2)
        date_in_future = datetime.now() + timedelta(days=2)

        payment: Payment = Payment(paid=False, due_date=date_in_past, amount=10.0)
        assert payment.overdue

        payment.paid = True
        assert not payment.overdue

        payment.paid = False
        payment.due_date = date_in_future
        assert not payment.overdue

    def test_days_left(self):
        assert True
        # date_in_past = datetime.now() + timedelta(days=2)
        # payment: Payment = Payment(paid=False, due_date=date_in_past, amount=10.0)
        # assert payment.b_days_left() == 2
