#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django import forms


class DateTimePickerInput(forms.TextInput):
    """
    时间管理插件的应用，用于时间选择
    """
    template_name = 'stark/forms/widgets/datetime_picker.html'
