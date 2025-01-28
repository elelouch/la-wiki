from typing import final
from django import forms

@final
class LoginForm (forms.Form):
    username = forms.CharField(label="username",max_length=200, required=True)
    password = forms.CharField(max_length=200, required=True)
