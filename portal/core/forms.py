from django.utils.translation import gettext_lazy as _
from typing import final
from django import forms
from django.core.validators import RegexValidator

@final
class SectionForm(forms.Form):
    id = forms.IntegerField(
        label="",
        widget=forms.NumberInput(
            attrs={
                "class":"hidden",
                "x-ref":"sectionFormId"
            }
        )
    )
    name = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            "placeholder":_("Section Name"),
            "class":"rounded-md"
            }),
        validators=[RegexValidator(code="404", message=_("Name is not valid"))],
        max_length=200,
        required=True
    )

@final
class FileForm(forms.Form):
    id = forms.IntegerField(
        label="",
        widget=forms.NumberInput(
            attrs={
                "class":"hidden",
                "x-ref":"sectionFormId"
            }
        )
    )
    file = forms.FileField(label="", required=True)
