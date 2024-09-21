from django import forms
from .models import FileModel, DateModel, ShowDataModel


class FileForm(forms.ModelForm):
    
    class Meta:
        model = FileModel
        fields = "__all__"

class DateForm(forms.ModelForm):
    date = forms.CharField(label="Дата", widget=forms.TextInput(attrs={"placeholder": "XX.XX.XXXX-XX.XX.XXXX"}))
    
    class Meta:
        model = DateModel
        fields = "__all__"

class ShablonForm(forms.Form):
    CHOICES = (
        ("DELETE", "Шаблон удаления",),
        ("CHECK", "Шаблон перепроверки",),
    )

    select = forms.ChoiceField(widget=forms.Select, choices=CHOICES)
    code = forms.CharField(widget=forms.Textarea(attrs={"rows":"5", "cols": "15", "style": "resize: both;"}))

class CheckBoxForm(forms.ModelForm):
    is_check = forms.BooleanField(label="", required=False)

    class Meta:
        model = ShowDataModel
        fields = ("is_check", )