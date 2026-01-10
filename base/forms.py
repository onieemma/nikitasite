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


from .models import FinancingInquiry

class MortgageCalculatorForm(forms.Form):
    home_price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '500000',
            'id': 'home_price'
        })
    )
    down_payment = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '100000',
            'id': 'down_payment'
        })
    )
    interest_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '6.5',
            'id': 'interest_rate',
            'step': '0.01'
        })
    )
    loan_term = forms.IntegerField(
        min_value=1,
        max_value=50,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '30',
            'id': 'loan_term'
        })
    )
    loan_type = forms.ChoiceField(
        choices=FinancingInquiry.LOAN_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-input',
            'id': 'loan_type'
        })
    )


class FinancingInquiryForm(forms.ModelForm):
    class Meta:
        model = FinancingInquiry
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'home_price', 'down_payment', 'interest_rate',
            'loan_term', 'loan_type', 'additional_notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '(123) 456-7890'
            }),
            'home_price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '500000',
                'readonly': 'readonly'
            }),
            'down_payment': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '100000',
                'readonly': 'readonly'
            }),
            'interest_rate': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '6.5',
                'readonly': 'readonly',
                'step': '0.01'
            }),
            'loan_term': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '30',
                'readonly': 'readonly'
            }),
            'loan_type': forms.Select(attrs={
                'class': 'form-input',
                'readonly': 'readonly'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Any additional information...',
                'rows': 4
            }),
        }

