from django.conf import settings
from rbac.models import Menu

def init_permission(current_user, request):
    '''
    初始化权限信息
    :param current_user: 当前登录用户
    :param request: 请求相关参数
    :return:
    '''
    # 当前用户所有权限
    permission_queryset = current_user.roles.filter(permissions__isnull=False).values(
        "permissions__id",
        "permissions__url",
        "permissions__name",
        "permissions__title",
        "permissions__pid",
        "permissions__pid__url",
        "permissions__pid__title",
        "permissions__menu__id",
        "permissions__menu__title",
        "permissions__menu__icon").distinct()

    # 获取权限中的url + 菜单信息
    menu_dict = {}
    permission_dict = {}
    for item in permission_queryset:
        permission_dict[item.get('permissions__name')] = {
            'id': item.get('permissions__id'),
            'url': item.get('permissions__url'),
            'pid': item.get('permissions__pid'),
            'title': item.get('permissions__title'),
            'p_title': item.get('permissions__pid__title'),
            'p_url': item.get('permissions__pid__url')
        }

        menu_id = item.get('permissions__menu__id')
        if not menu_id:
            continue

        node = {'title': item.get('permissions__title'), 'url': item.get("permissions__url"), 'id': item.get('permissions__id')}
        if menu_id not in menu_dict.keys():
            menu_dict[menu_id] = {
                'title': item.get('permissions__menu__title'),
                'icon': item.get('permissions__menu__icon'),
                'children': [node]
            }
        else:
            menu_dict[menu_id]['children'].append(node)

    print(menu_dict)
    # 放入session中
    request.session[settings.PERMISSION_SESSION_KEY] = permission_dict
    request.session[settings.MENU_SESSION_KEY] = menu_dict


