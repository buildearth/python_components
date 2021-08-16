from django import forms
from django.utils.safestring import mark_safe

from rbac import models
from rbac.forms.base import BootStrapModelForm


class MenuModelForm(forms.ModelForm):
    class Meta:
        model = models.Menu
        fields = ['title', 'icon']
        widgets = {
            'icon': forms.RadioSelect(
                choices=[
                    ['fa-user-circle', mark_safe('<i class="fa fa-user-circle" aria-hidden="true"></i>')],
                    ['fa-handshake-o', mark_safe('<i class="fa fa-handshake-o" aria-hidden="true"></i>')],
                    ['fa-window-restore', mark_safe('<i class="fa fa-window-restore" aria-hidden="true"></i>')],
                    ['fa-bell', mark_safe('<i class="fa fa-bell" aria-hidden="true"></i>')],
                    ['fa-bed', mark_safe('<i class="fa fa-bed" aria-hidden="true"></i>')]
                ]
            ),
            'title': forms.TextInput(attrs={'class': 'form-control'})
        }
    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for name, field in self.fields.items():
    #         field.widget.attrs['class'] = 'form-control'


class SecondMenuModelForm(BootStrapModelForm):
    class Meta:
        model = models.Permission
        fields = ["title", "url", "name", "menu"]


class PermissionMenuModelForm(BootStrapModelForm):
    class Meta:
        model = models.Permission
        fields = ["title", "url", "name"]


class MultiAddPermissionForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    url = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    menu_id = forms.ChoiceField(choices=[(None, '------')],
                                widget=forms.Select(attrs={'class': 'form-control'}),
                                required=False)

    pid_id = forms.ChoiceField(choices=[(None, '------')],
                               widget=forms.Select(attrs={'class': 'form-control'}),
                               required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给Choice中动态添加数据库中的数据
        self.fields['menu_id'].choices += models.Menu.objects.all().values_list('id', 'title')
        self.fields['pid_id'].choices += models.Permission.objects.filter(
            pid__isnull=True).exclude(menu__isnull=True).values_list('id', 'title')


class MultiEditPermissionForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    url = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    menu_id = forms.ChoiceField(choices=[(None, '------')],
                                widget=forms.Select(attrs={'class': 'form-control'}),
                                required=False)

    pid_id = forms.ChoiceField(choices=[(None, '------')],
                               widget=forms.Select(attrs={'class': 'form-control'}),
                               required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给Choice中动态添加数据库中的数据
        self.fields['menu_id'].choices += models.Menu.objects.all().values_list('id', 'title')
        self.fields['pid_id'].choices += models.Permission.objects.filter(
            pid__isnull=True).exclude(menu__isnull=True).values_list('id', 'title')