from django import forms
from apps.users.models import ClientProfile
from apps.logistics.models import Shipment, ShipmentStatus, ShipmentCategory, ShipmentItem, ShipmentExpense


class ClientForm(forms.ModelForm):
    class Meta:
        model = ClientProfile
        fields = ['first_name', 'last_name', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'crm-form-input', 'placeholder': 'Имя клиента',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'crm-form-input', 'placeholder': 'Фамилия клиента',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'crm-form-input', 'placeholder': '+996 XXX XXX XXX',
            }),
        }


class ShipmentForm(forms.ModelForm):
    client_code = forms.CharField(
        label='Код клиента',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'crm-form-input',
            'placeholder': 'Например: 123',
        }),
    )

    class Meta:
        model = Shipment
        fields = ['category', 'delivery_address', 'notes']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'crm-form-select',
            }),
            'delivery_address': forms.TextInput(attrs={
                'class': 'crm-form-input',
                'placeholder': 'Например: Москва',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'crm-form-textarea', 'placeholder': 'Примечания (необязательно)', 'rows': 3,
            }),
        }

    def clean_client_code(self):
        code = self.cleaned_data['client_code'].strip()
        try:
            ClientProfile.objects.get(client_code=code)
        except ClientProfile.DoesNotExist:
            raise forms.ValidationError(f'Клиент с кодом «{code}» не найден.')
        return code


class ShipmentItemForm(forms.ModelForm):
    class Meta:
        model = ShipmentItem
        fields = ['service_name', 'product_name', 'places_count', 'units_count', 'weight', 'service_price']
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'crm-form-input', 'placeholder': 'Услуга по доставке товара'}),
            'product_name': forms.TextInput(attrs={'class': 'crm-form-input', 'placeholder': 'Например: Женские платья'}),
            'places_count': forms.NumberInput(attrs={'class': 'crm-form-input', 'placeholder': 'Мест', 'min': '1'}),
            'units_count': forms.NumberInput(attrs={'class': 'crm-form-input', 'placeholder': 'Шт.', 'min': '1'}),
            'weight': forms.NumberInput(attrs={'class': 'crm-form-input', 'placeholder': 'Вес', 'step': '0.01'}),
            'service_price': forms.NumberInput(attrs={'class': 'crm-form-input', 'placeholder': 'Стоимость услуги', 'step': '0.01'}),
        }


class ShipmentExpenseForm(forms.ModelForm):
    class Meta:
        model = ShipmentExpense
        fields = ['name', 'quantity', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'crm-form-input', 'placeholder': 'Например: Средний мешок'}),
            'quantity': forms.NumberInput(attrs={'class': 'crm-form-input', 'placeholder': 'Количество', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'crm-form-input', 'placeholder': 'Цена', 'step': '0.01'}),
        }


class ShipmentStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=ShipmentStatus.choices,
        widget=forms.Select(attrs={'class': 'crm-form-select'}),
        label='Новый статус',
    )
