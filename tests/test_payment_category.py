from payment import Payment
from payment_category import PaymentCategory


class TestPaymentCategory:
    def test_str_and_has_payments(self):
        cat = PaymentCategory(name="Utilities", column="C")
        assert str(cat) == "Utilities"
        assert not cat.has_payments()

        # Add a dummy payment and verify state changes
        pmt = Payment()
        cat.payments["2025-1"] = pmt
        assert cat.has_payments()
