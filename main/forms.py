from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")


class LoginForm(AuthenticationForm):
    pass


class ProductSearchForm(forms.Form):
    keyword = forms.CharField(
        label="検索",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "商品の検索"}),
    )


class ProductNumForm(forms.Form):
    num = forms.IntegerField(
        label="数量",
        max_value=500,
        min_value=1,
        required=True,
        initial=1,
    )
