from django.utils.translation import gettext_lazy as _
from typing import final
from django import forms
from django.core.validators import RegexValidator
from core.models import Section

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

@final
class UserForm(forms.Form):
    id = forms.IntegerField(
            initial=forms.ChoiceField(),
            label="",
            widget=forms.NumberInput(attrs={"class":"hidden"})
            )
    main_section = forms.ModelChoiceField(
            label="",
            queryset=Section.objects.all(),
            to_field_name="id",
            required=True,
            widget=forms.Select(attrs={})
            )
    email = forms.CharField(
            label="",
            widget=forms.TextInput(attrs={
                "placeholder":_("Email"),
                "class":"rounded-md"
                }),
            validators=[RegexValidator(code="404", message=_("Email is not valid"))],
            max_length=200,
            required=True
            )
    username = forms.CharField(
            label="",
            widget=forms.TextInput(attrs={
                "placeholder":_("Username"),
                "class":"rounded-md"
                }),
            validators=[RegexValidator(code="404", message=_("Username is not valid"))],
            max_length=200,
            required=True
            )
    password = forms.CharField(
            label="",
            widget=forms.PasswordInput(
                attrs={
                    "placeholder":_("Password"),
                    "class":"rounded-md"
                    }),
                validators=[
                    RegexValidator(
                        r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$",
                        code="404", 
                        message=_("Password is not valid")
                        )
                    ],
                max_length=200,
                required=True
            )
    password = forms.CharField(
            label="",
            widget=forms.PasswordInput(attrs={
                "placeholder":_("First Name"),
                "class":"rounded-md"
                }),
            max_length=200,
            required=True
            )
    last_name = forms.CharField(
            label="",
            widget=forms.PasswordInput(attrs={
                "placeholder":_("Last Name"),
                "class":"rounded-md"
                }),
            max_length=200,
            required=True
            )
