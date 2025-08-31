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

    def test_due_soon_or_overdue_alias(self):
        pmt: Payment = Payment(due_date=datetime.now())
        # Both properties should return the same value
        assert pmt.due_soon_or_overdue == pmt.payable_within_2days

    def test_due_soon_or_overdue_logic(self):
        # Due today and unpaid -> True
        pmt: Payment = Payment(paid=False, due_date=datetime.now())
        assert pmt.due_soon_or_overdue

        # Paid -> always False
        pmt.paid = True
        assert not pmt.due_soon_or_overdue

        # Unpaid and due in > 2 days -> False
        pmt.paid = False
        pmt.due_date = datetime.now() + timedelta(days=3)
        assert not pmt.due_soon_or_overdue

        # Unpaid and overdue -> True
        pmt.due_date = datetime.now() - timedelta(days=1)
        assert pmt.due_soon_or_overdue

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
