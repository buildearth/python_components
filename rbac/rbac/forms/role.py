from django.core.exceptions import ValidationError

from django import forms
from rbac import models


class RoleModelForm(forms.ModelForm):
    class Meta:
        model = models.Role
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'})
        }


class UserModelForm(forms.ModelForm):
    confirm_password = forms.CharField(label='确认密码', widget=forms.TextInput(attrs={'type': 'password'}))

    class Meta:
        model = models.UserInfo
        fields = ["name", "email", "password", 'confirm_password']
        widgets = {
            'password': forms.TextInput(attrs={'type': 'password'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 统一给ModelForm生成的字段添加样式
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise ValidationError('两次密码不一致')

        return confirm_password


class UpdateUserModelForm(forms.ModelForm):
    class Meta:
        model = models.UserInfo
        fields = ['name', 'email']
        # 手动给每个字段添加样式
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ResetPasswordUserModelForm(forms.ModelForm):
    confirm_password = forms.CharField(label='确认密码', widget=forms.TextInput(attrs={'type': 'password'}))

    class Meta:
        model = models.UserInfo
        fields = ["password", 'confirm_password']
        widgets = {
            'password': forms.TextInput(attrs={'type': 'password'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 统一给ModelForm生成的字段添加样式
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise ValidationError('两次密码不一致')

        return confirm_password




