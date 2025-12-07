from decimal import Decimal
from django import forms

class InvestmentInputForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Investment amount"
    )
    compounding = forms.ChoiceField(
        choices=[("annual", "Annual"), ("monthly", "Monthly")],
        initial="annual",
        required=False,
        label="Compounding"
    )