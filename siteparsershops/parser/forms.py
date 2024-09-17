from django import forms
from .models import FileModel, DateModel


class FileForm(forms.ModelForm):
    
    class Meta:
        model = FileModel
        fields = "__all__"

class DateForm(forms.ModelForm):
    date = forms.CharField(label="Дата", widget=forms.TextInput(attrs={"placeholder": "XX.XX.XXXX-XX.XX.XXXX"}))
    
    class Meta:
        model = DateModel
        fields = "__all__"