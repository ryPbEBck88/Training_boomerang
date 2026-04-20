from decimal import Decimal

from django import forms
from django.contrib import admin

from .models import StaffWallet


class StaffWalletAdminForm(forms.ModelForm):
    top_up_amount = forms.DecimalField(
        label='Сумма пополнения',
        required=False,
        min_value=Decimal('0.01'),
        decimal_places=2,
        max_digits=12,
        help_text='Если указать сумму, она будет добавлена к текущему балансу при сохранении.',
    )

    class Meta:
        model = StaffWallet
        fields = '__all__'


@admin.register(StaffWallet)
class StaffWalletAdmin(admin.ModelAdmin):
    form = StaffWalletAdminForm
    list_display = ('user', 'balance', 'updated_at')
    list_editable = ('balance',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user',)

    def save_model(self, request, obj, form, change):
        top_up_amount = form.cleaned_data.get('top_up_amount')
        if top_up_amount:
            current_balance = Decimal('0.00')
            if change and obj.pk:
                current_balance = (
                    StaffWallet.objects
                    .filter(pk=obj.pk)
                    .values_list('balance', flat=True)
                    .first()
                    or Decimal('0.00')
                )
            obj.balance = (current_balance + top_up_amount).quantize(Decimal('0.01'))
        super().save_model(request, obj, form, change)
