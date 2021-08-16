import re

from django.template import Library
from django.conf import settings
from django.urls import reverse
from django.http import QueryDict

from collections import OrderedDict

from rbac.service import urls

register = Library()

@register.inclusion_tag('rbac/static_menu.html')
def static_menu(request):
    """
    创建一级菜单
    :return:
    """
    menu_list = request.session.get(settings.MENU_SESSION_KEY)
    print(menu_list)

    return {'menu_list': menu_list}


@register.inclusion_tag('rbac/multi_menu.html')
def multi_menu(request):
    """
    创建二级菜单
    :param request:
    :return:
    """
    menu_dict = request.session.get(settings.MENU_SESSION_KEY)

    # 字典排序, 从session中拿到的是一个字典，他的顺序是不确定的，会导致菜单显示顺序偶尔不一致，要解决这个问题需要对拿出来的字典进行排序
    key_list = sorted(menu_dict)

    ordered_dict = OrderedDict()
    for key in key_list:
        val = menu_dict[key]
        val['class'] = 'hide'  # 用来设置，二级菜单默认的class样式为hide，不显示
        for per in val['children']:

            if per.get('id') == request.current_selected_permission:
                per['class'] = 'active'  # 判断是当前url对应的二级菜单，将二级菜单显示为激活状态
                val['class'] = ''  # 某个一级菜单下，有一个是激活状态，将二级菜单默认class样式置空，即能显示其他二级菜单
        ordered_dict[key] = val

    return {"menu_dict": ordered_dict}


@register.inclusion_tag('rbac/record_list.html')
def record_list(request):
    return {'record_list': request.url_record}


@register.filter
def has_permission(request, name):
    """
    判断是否有权限
    :param request:
    :param name:
    :return:
    """
    if name in request.session.get(settings.PERMISSION_SESSION_KEY):
        return True

    return False


@register.simple_tag
def memory_url(request, name, *args, **kwargs):
    """
    生成带有原搜索条件的url，替代了原来模板中的url
    :param request:
    :param name:
    :return:
    """
    return urls.memory_url(request, name, *args, **kwargs)
