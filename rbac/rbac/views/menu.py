from collections import OrderedDict

from django.shortcuts import render, redirect, HttpResponse
from django.forms import formset_factory
from django.utils.module_loading import import_string
from django.conf import settings

from rbac import models
from rbac.forms.menu import MenuModelForm, SecondMenuModelForm, PermissionMenuModelForm, MultiAddPermissionForm, MultiEditPermissionForm

from rbac.service.urls import memory_reverse
from rbac.service.routes import get_all_url_dict


def menu_list(request):
    """
    菜单和权限列表
    :param request:
    :return:
    """
    menus = models.Menu.objects.all()
    menu_id = request.GET.get('mid')
    second_menu_id = request.GET.get('sid')

    # 检查menu_id的正确性
    if not models.Menu.objects.filter(pk=menu_id).exists():
        menu_id = None
    # 检查second_menu_id在Permission表中是否存在
    if not models.Permission.objects.filter(pk=second_menu_id).exists():
        second_menu_id = None

    second_menus = []
    permissions = []
    if menu_id:
        # 获取一级菜但下的二级菜单
        second_menus = models.Permission.objects.filter(menu=menu_id)
    if second_menu_id:
        # 获取二级菜单下的所有权限
        permissions = models.Permission.objects.filter(pid_id=second_menu_id)

    return render(
        request,
        'rbac/menu_list.html',
        {
            'menus': menus,
            'mid': menu_id,
            'second_menus': second_menus,
            'sid': second_menu_id,
            'permissions': permissions,
        }
    )


def menu_add(request):
    """
    新增一级菜单
    :param request:
    :return:
    """
    if request.method == 'GET':
        form = MenuModelForm()
        return render(request, 'rbac/change.html', {'form': form})

    form = MenuModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(memory_reverse(request, 'rbac:menu_list'))

    # 验证失败的返回
    return render(request, 'rbac/change.html', {'form': form})


def menu_edit(request, pk):
    """
    修改一级菜单
    :param request:
    :return:
    """
    obj = models.Menu.objects.filter(id=pk).first()
    if not obj:
        return HttpResponse('角色不存在')

    if request.method == 'GET':
        form = MenuModelForm(instance=obj)
        return render(request, 'rbac/change.html', {'form': form})

    form = MenuModelForm(instance=obj, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(memory_reverse(request, 'rbac:menu_list'))
    return render(request, 'rbac/change.html', {'form': form})


def menu_del(request, pk):
    """
    一级菜单删除
    :param request:
    :param pk:要被删除的菜单id
    :return:
    """
    basic_url = memory_reverse(request, 'rbac:menu_list')

    if request.method == "GET":
        return render(request, 'rbac/delete.html', {'cancel_url': basic_url})

    models.Menu.objects.filter(id=pk).delete()
    return redirect(basic_url)


def second_menu_add(request, menu_id):
    """
    增加二级菜单
    :param request:
    :param menu_id: 已选择的一级菜单id,用于设置默认值
    :return:
    """
    menu_obj = models.Menu.objects.filter(pk=menu_id).first()
    if request.method == 'GET':
        # 给设置默认值
        form = SecondMenuModelForm(initial={'menu': menu_obj})
        return render(request, 'rbac/change.html', {'form': form})

    form = SecondMenuModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(memory_reverse(request, 'rbac:menu_list'))

    # 验证失败的返回
    return render(request, 'rbac/change.html', {'form': form})


def second_menu_edit(request, pk):
    """
    修改二级菜单
    :param request:
    :return:
    """
    obj = models.Permission.objects.filter(id=pk).first()
    if not obj:
        return HttpResponse('菜单不存在')

    if request.method == 'GET':
        form = SecondMenuModelForm(instance=obj)
        return render(request, 'rbac/change.html', {'form': form})

    form = SecondMenuModelForm(instance=obj, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(memory_reverse(request, 'rbac:menu_list'))
    return render(request, 'rbac/change.html', {'form': form})


def second_menu_del(request, pk):
    """
    二级菜单删除
    :param request:
    :param pk:要被删除的菜单id
    :return:
    """
    basic_url = memory_reverse(request, 'rbac:menu_list')

    if request.method == "GET":
        return render(request, 'rbac/delete.html', {'cancel_url': basic_url})

    models.Permission.objects.filter(id=pk).delete()
    return redirect(basic_url)


def permission_add(request, second_menu_id):
    """
    二级菜单下的权限增加
    :param request:
    :param second_menu_id:
    :return:
    """
    second_menu_obj = models.Permission.objects.filter(pk=second_menu_id).first()
    # 判断二级菜单是否存在
    if not second_menu_obj:
        return HttpResponse('二级菜单不存在')

    if request.method == "GET":
        form = PermissionMenuModelForm()
        return render(request, 'rbac/change.html', {'form': form})

    form = PermissionMenuModelForm(request.POST)
    if form.is_valid():
        # 将二级菜单传入到用户传入的对象中

        '''
            form.instance中包含用户提交的所有值,其机制是：
            1. instance = models.Permission(title='xx', name='xx', url='xx')
            2. instance.pid = second_menu_obj  给用户传入的数据添加值
            3. instance.save() 保存数据
        '''
        form.instance.pid = second_menu_obj
        form.save()
        return redirect(memory_reverse(request, 'rbac:menu_list'))

    # 验证失败的返回
    return render(request, 'rbac/change.html', {'form': form})


def permission_edit(request, pk):
    """
    二级菜单下的权限编辑
    :param request:
    :param second_menu_id:
    :return:
    """
    permission_obj = models.Permission.objects.filter(pk=pk).first()
    # 判断二级菜单是否存在
    if not permission_obj:
        return HttpResponse('二级菜单不存在')

    if request.method == "GET":
        form = PermissionMenuModelForm(instance=permission_obj)
        return render(request, 'rbac/change.html', {'form': form})

    form = SecondMenuModelForm(instance=permission_obj, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(memory_reverse(request, 'rbac:menu_list'))

    # 验证失败的返回
    return render(request, 'rbac/change.html', {'form': form})


def permission_del(request, pk):
    """
    二级菜单下权限删除
    :param request:
    :param pk:
    :return:
    """
    basic_url = memory_reverse(request, 'rbac:menu_list')

    if request.method == "GET":
        return render(request, 'rbac/delete.html', {'cancel_url': basic_url})

    models.Permission.objects.filter(id=pk).delete()
    return redirect(basic_url)


def multi_permissions(request):
    """
    批量操作权限
    :param request:
    :return:
    """
    post_type = request.GET.get('type')  # 页面上新增和更新都是提交的post请求，增加参数来判断是新增还是更新

    generate_formset_class = formset_factory(MultiAddPermissionForm, extra=0)
    update_formset_class = formset_factory(MultiEditPermissionForm, extra=0)

    generate_formset = None
    update_formset = None
    print(post_type, request.method)
    if request.method == 'POST' and post_type == 'generate':
        # 新增
        formset = generate_formset_class(data=request.POST)
        if formset.is_valid():
            has_error = False  # 用于判断是否所以数据都正确可存储到数据库
            post_row_list = formset.cleaned_data
            add_object_list = []  # 存储没有问题的数据对象
            for i in range(formset.total_form_count()):
                row_dict = post_row_list[i]
                try:
                    obj = models.Permission(**row_dict)
                    obj.validate_unique()
                    add_object_list.append(obj)
                except Exception as e:
                    formset.errors[i].update(e)
                    # 有错误信息的formset 传递到前端显示
                    generate_formset = formset
                    has_error = True
            if not has_error:
                # 所有的新增内容检测没有问题，才进行更新到数据库
                models.Permission.objects.bulk_create(add_object_list, batch_size=100)
        else:
            # 有错误信息的formset 传递到前端显示
            generate_formset = formset

    if request.method == 'POST' and post_type == 'update':
        # 更新
        formset = update_formset_class(data=request.POST)
        if formset.is_valid():
            post_row_list = formset.cleaned_data
            for i in range(formset.total_form_count()):
                row_dict = post_row_list[i]
                permission_id = row_dict.pop('id')
                try:
                    row_obj = models.Permission.objects.filter(pk=permission_id).first()
                    for key, value in row_dict.items():
                        setattr(row_obj, key, value)
                    row_obj.validate_unique()
                    row_obj.save()
                except Exception as e:
                    formset.errors[i].update(e)
                    update_formset = formset
        else:
            # 带有错误信息的formset,没有通过验证，显示错误信息
            update_formset = formset

    # 获取项目中所有的url
    url_ordered_dict = get_all_url_dict()
    router_name_set = set(url_ordered_dict.keys())
    # 获取数据库中所有的url
    permissions = models.Permission.objects.all().values('id', 'title', 'name', 'url', 'menu_id', 'pid_id')
    permissions_dict = OrderedDict()
    for row in permissions:
        permissions_dict[row.get('name')] = row
    # print(permissions_dict)
    permission_name_set = set(permissions_dict.keys())

    for name, value in permissions_dict.items():
        router_row_dict = url_ordered_dict.get(name)
        if not router_row_dict:
            # 数据库中有，自动发现的没有
            continue
        # 数据库和自动发现的都有，判断两者的url是否一致
        if value['url'] != router_row_dict['url']:
            print('数据库：{}({}) <==> 自动发现：{}({})'.format(value['url'], value['name'], router_row_dict['url'], router_row_dict['name']))
            value['url'] = "路由和数据库中不一致"


    # 应该添加、删除、修改的权限有哪些？
    # 添加 差集
    if not generate_formset:
        generate_name_list = router_name_set - permission_name_set
        generate_formset = generate_formset_class(
            initial=[row_dict for name, row_dict in url_ordered_dict.items() if name in generate_name_list]
        )

    # 删除 差集
    delete_name_list = permission_name_set - router_name_set
    delete_row_list = [row_dict for name, row_dict in permissions_dict.items() if name in delete_name_list]

    # print(delete_row_list)
    # 更新 交集
    if not update_formset:
        update_name_list = permission_name_set & router_name_set

        update_formset = update_formset_class(
            initial=[row_dict for name, row_dict in permissions_dict.items() if name in update_name_list]
        )

    return render(request,
                  'rbac/multi_permissions.html',
                  {
                      'generate_formset': generate_formset,
                      'delete_row_list': delete_row_list,
                      'update_formset': update_formset
                  }
                  )


def multi_permissions_del(request, pk):
    """
    批量权限管理页面的权限删除
    :param request:
    :param pk:
    :return:
    """
    basic_url = memory_reverse(request, 'rbac:multi_permissions')

    if request.method == "GET":
        return render(request, 'rbac/delete.html', {'cancel_url': basic_url})

    models.Permission.objects.filter(id=pk).delete()
    return redirect(basic_url)


def distribute_permissions(request):
    user_model_class = import_string(settings.RBAC_USER_MODLE_CLASS)

    user_id = request.GET.get('uid')
    role_id = request.GET.get('rid')
    # user_obj = models.UserInfo.objects.filter(pk=user_id).first()
    user_obj = user_model_class.objects.filter(pk=user_id).first()
    role_obj = models.Role.objects.filter(pk=role_id).first()
    if not user_obj:
        user_id = None
    if not role_obj:
        role_id = None

    # 检测表单提交的是角色还是权限
    if request.method == "POST" and request.POST.get('type') == "role":
        role_id_list = request.POST.getlist('roles')
        if not user_obj:
            return HttpResponse('请选择用户，再分配角色')
        user_obj.roles.set(role_id_list)

    if request.method == "POST" and request.POST.get('type') == "permission":
        permission_id_list = request.POST.getlist('permissions')
        if not role_obj:
            return HttpResponse('请选择角色，再分配权限')
        role_obj.permissions.set(permission_id_list)

    # 筛选出当前用户拥有的角色
    if user_id:
        user_has_roles = user_obj.roles.all()
    else:
        user_has_roles = []
    user_has_roles_dict = {item.id: None for item in user_has_roles}
    # 筛选出当前用户拥有的权限
    # 如果选中了角色，优先显示选中角色所有的权限；如果没有选中角色，才显示用户所拥有的权限
    if role_obj:  # 选择了角色
        user_has_permissions = role_obj.permissions.values('id')
        user_has_permissions_dict = {item['id']: None for item in user_has_permissions}
    elif user_obj:  # 选择了用户，没有选择角色
        user_has_permissions = user_obj.roles.filter(permissions__id__isnull=False).values('id',
                                                                                           'permissions').distinct()
        user_has_permissions_dict = {item['permissions']: None for item in user_has_permissions}
    else:
        user_has_permissions_dict = {}

    # all_users_list = models.UserInfo.objects.all()
    all_users_list = user_model_class.objects.all()
    all_roles_list = models.Role.objects.all()
    # 所有的一级菜单
    all_menu_list = models.Menu.objects.values('id', 'title')
    # 所有二级菜单
    all_second_menu_list = models.Permission.objects.filter(menu__isnull=False).values('id', 'title', 'menu_id')
    # 所有三级菜单
    all_permission_list = models.Permission.objects.filter(menu__isnull=True).values('id', 'title', 'pid_id')

    # 使用字典来同步更新列表中的值，key对应的value和列表中的元素指向的是同一块内存地址。
    all_menu_dict = {}
    all_second_menu_dict = {}
    for item in all_menu_list:
        item['children'] = []
        all_menu_dict[item['id']] = item

    # 二级菜单挂靠到一级菜单下
    for row in all_second_menu_list:
        row['children'] = []
        menu_id = row.get('menu_id')
        all_second_menu_dict[row['id']] = row
        all_menu_dict[menu_id]['children'].append(row)

    # 不能做菜单的权限挂靠到二级菜单
    for row in all_permission_list:
        pid_id = row.get('pid_id')
        if pid_id:
            all_second_menu_dict[pid_id]['children'].append(row)


    return render(
        request,
        'rbac/distribute_permissions.html',
        {
            'user_list': all_users_list,
            'role_list': all_roles_list,
            'menu_list': all_menu_list,
            'user_id': user_id,
            'role_id': role_id,
            'user_has_roles_dict': user_has_roles_dict,
            'user_has_permissions_dict': user_has_permissions_dict,
        },
    )