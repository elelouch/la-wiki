from django.utils.translation import gettext_lazy as _
from typing import final
from django import forms
from django.core.validators import RegexValidator

@final
class SectionForm(forms.Form):
    username_regex = r"^[0-9A-Za-z]{6,16}$"

    name = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            "placeholder":_("Section Name"),
            "class":"rounded-md"
            }),
        validators=[RegexValidator(regex=username_regex,code="404", message=_("Name is not valid"))],
        max_length=200,
        required=True
    )
