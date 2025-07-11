from django.utils.translation import gettext_lazy as _
from typing import final
from django import forms
from django.core.validators import MaxLengthValidator, MinLengthValidator, MinValueValidator, RegexValidator

@final
class SectionForm(forms.Form):
    root_id = forms.IntegerField(
        label="",
        widget=forms.NumberInput(attrs={
            "class":"hidden",
        }),
        validators=[MinValueValidator(1)],
        required=True
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
    root_id = forms.IntegerField(
        label="",
        widget = forms.NumberInput(attrs={
            "class": "hidden",
        }),
        validators=[MinValueValidator(1)],
        required=True
    )
    file = forms.FileField(label="", required=True)

@final
class SearchForm(forms.Form):
    name = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            "x-ref":"modalSearchInput",
            "placeholder":_("Search an archive"),
            "autocomplete":"off",
            "class":"rounded-md"
        }),
        validators=[RegexValidator(code="404", message=_("Name is not valid"))],
        max_length=200,
        required=True
    )
    by_content = forms.BooleanField(required=False)

@final
class MarkdownForm(forms.Form):
    markdown_length = 4 * 1024 * 1024
    root_id = forms.IntegerField(
        label="",
        widget = forms.NumberInput(attrs={
            "class": "hidden",
        }),
        validators=[MinValueValidator(1)],
        required=True
    )
    name = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={
            "placeholder":_("File Name"),
            "class":"rounded-md"
        }),
        validators=[RegexValidator(code="404", message=_("Name is not valid"))],
        max_length=200,
        required=True
    )
    file = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={
            "placeholder":_("Markdown supported"),
            "class":"rounded-md"
        }),
        validators = [MaxLengthValidator(markdown_length), MinLengthValidator(1)],
        required=True
    )

