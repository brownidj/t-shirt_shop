from django import forms

from .models import DesignRequest


class DesignRequestForm(forms.ModelForm):
    class Meta:
        model = DesignRequest
        fields = ("name", "email", "details")
        widgets = {
            "details": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "details": "Tell us about the design you would like",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            if name == "name":
                field.widget.attrs["placeholder"] = "Your name"
            elif name == "email":
                field.widget.attrs["placeholder"] = "Your email"

    def save(self, commit=True):
        request = super().save(commit=False)
        request.idea = request.details[:200]
        if commit:
            request.save()
        return request
