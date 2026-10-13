from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.exceptions import ValidationError

User = get_user_model()


class EmailContinueForm(forms.Form):
    """Шаг 1 регистрации / входа: email (или логин на входе)."""

    email = forms.CharField(
        label='Электронная почта',
        required=True,
        widget=forms.EmailInput(
            attrs={
                'autocomplete': 'email',
                'class': 'auth-gate-input',
                'placeholder': 'Электронная почта',
                'inputmode': 'email',
            }
        ),
    )
    hp_field = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_hp_field(self):
        val = (self.cleaned_data.get('hp_field') or '').strip()
        if val:
            raise ValidationError('Проверка не пройдена.')
        return ''

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email or '@' not in email:
            raise ValidationError('Укажите корректный адрес почты.')
        return email


class LoginIdentifierForm(forms.Form):
    """Шаг 1 входа: email или имя пользователя."""

    identifier = forms.CharField(
        label='Электронная почта или логин',
        required=True,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'username',
                'class': 'auth-gate-input',
                'placeholder': 'Электронная почта или логин',
            }
        ),
    )
    hp_field = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_hp_field(self):
        val = (self.cleaned_data.get('hp_field') or '').strip()
        if val:
            raise ValidationError('Проверка не пройдена.')
        return ''

    def clean_identifier(self):
        value = (self.cleaned_data.get('identifier') or '').strip()
        if not value:
            raise ValidationError('Укажите почту или имя пользователя.')
        return value


class SignUpDetailsForm(UserCreationForm):
    """Шаг 2 регистрации: логин и пароль (email уже в session)."""

    hp_field = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, email=None, **kwargs):
        self.fixed_email = (email or '').strip().lower()
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Пароль ещё раз'
        self.fields['username'].widget.attrs.update(
            {'class': 'auth-gate-input', 'autocomplete': 'username', 'placeholder': 'Имя пользователя'}
        )
        self.fields['password1'].widget.attrs.update(
            {'class': 'auth-gate-input', 'autocomplete': 'new-password', 'placeholder': 'Пароль'}
        )
        self.fields['password2'].widget.attrs.update(
            {'class': 'auth-gate-input', 'autocomplete': 'new-password', 'placeholder': 'Пароль ещё раз'}
        )
        self.fields['username'].help_text = (
            'Латинские буквы, цифры и @/./+/-/_.'
        )

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('Укажите имя пользователя.')
        validator = ASCIIUsernameValidator()
        try:
            validator(username)
        except ValidationError:
            raise ValidationError(
                'Имя пользователя содержит недопустимые символы. '
                'Используйте латинские буквы, цифры и @/./+/-/_.'
            )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Это имя пользователя уже занято.')
        return username

    def clean_hp_field(self):
        val = (self.cleaned_data.get('hp_field') or '').strip()
        if val:
            raise ValidationError('Проверка не пройдена.')
        return ''

    def clean(self):
        cleaned = super().clean()
        if not self.fixed_email:
            raise ValidationError('Сначала укажите электронную почту.')
        if User.objects.filter(email__iexact=self.fixed_email).exists():
            raise ValidationError('Этот адрес уже используется. Войдите или укажите другую почту.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.fixed_email
        user.is_active = False
        if commit:
            user.save()
        return user


class SignUpForm(UserCreationForm):
    """Полная форма (совместимость / админские сценарии)."""

    hp_field = forms.CharField(required=False, widget=forms.HiddenInput())
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
        self.fields['username'].help_text = (
            'Разрешены только латинские буквы, цифры и символы @/./+/-/_. '
            'Пробелы и кириллица недопустимы.'
        )

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('Укажите имя пользователя.')
        validator = ASCIIUsernameValidator()
        try:
            validator(username)
        except ValidationError:
            raise ValidationError(
                'Имя пользователя содержит недопустимые символы. '
                'Используйте латинские буквы, цифры и @/./+/-/_.'
            )
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Это имя пользователя уже занято.')
        return username

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Укажите адрес почты.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Этот адрес уже используется. Войдите или укажите другую почту.')
        return email

    def clean_hp_field(self):
        val = (self.cleaned_data.get('hp_field') or '').strip()
        if val:
            raise ValidationError('Проверка не пройдена.')
        return ''

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
        self.fields['username'].label = 'Имя пользователя или почта'
        self.fields['password'].label = 'Пароль'
        self.fields['username'].widget.attrs.update(
            {
                'class': 'auth-gate-input',
                'autocomplete': 'username',
                'placeholder': 'Имя пользователя или почта',
            }
        )
        self.fields['password'].widget.attrs.update(
            {
                'class': 'auth-gate-input',
                'autocomplete': 'current-password',
                'placeholder': 'Пароль',
            }
        )


class LoginPasswordForm(forms.Form):
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'auth-gate-input',
                'autocomplete': 'current-password',
                'placeholder': 'Пароль',
            }
        ),
    )
