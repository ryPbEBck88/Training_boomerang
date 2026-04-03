from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

User = get_user_model()


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        label='Электронная почта',
        required=True,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'auth-input'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Пароль ещё раз'
        self.fields['username'].widget.attrs.update({'class': 'auth-input', 'autocomplete': 'username'})
        self.fields['password1'].widget.attrs.update({'class': 'auth-input', 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'class': 'auth-input', 'autocomplete': 'new-password'})

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Укажите адрес почты.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Этот адрес уже используется. Войдите или укажите другую почту.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False
        if commit:
            user.save()
        return user


class SiteLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password'].label = 'Пароль'
        self.fields['username'].widget.attrs.update({'class': 'auth-input', 'autocomplete': 'username'})
        self.fields['password'].widget.attrs.update({'class': 'auth-input', 'autocomplete': 'current-password'})
