from django.utils.translation import gettext_lazy as _
from typing import final
from django import forms
from django.core.validators import RegexValidator

@final
class LoginForm (forms.Form):
    username_regex = r"^[0-9A-Za-z]{6,16}$"

    username = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            "placeholder":_("User"),
            "class":"rounded-md"
            }),
        validators=[RegexValidator(regex=username_regex,code="404", message=_("User is not valid"))],
        max_length=200,
        required=True
    )
    password = forms.CharField(
        label="",
        widget=forms.PasswordInput(attrs={
            "placeholder":_("Password"),
            "class":"rounded-md"
            }),
        max_length=200,
        required=True
    )

