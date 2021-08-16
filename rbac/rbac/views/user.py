from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse

from rbac import models
from rbac.forms.role import UserModelForm, UpdateUserModelForm, ResetPasswordUserModelForm


def user_list(request):
    """
    用户列表
    :param request:
    :return:
    """
    user_queryset = models.UserInfo.objects.all()
    return render(request, 'rbac/user_list.html', {'users': user_queryset})


def user_add(request):
    """
    增加用户
    :param request:
    :return:
    """
    if request.method == 'GET':
        form = UserModelForm()
        return render(request, 'rbac/change.html', {'form': form})

    form = UserModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(reverse('rbac:user_list'))

    # 验证失败的返回
    return render(request, 'rbac/change.html', {'form': form})


def user_edit(request, pk):
    """
    修改用户
    :param request:
    :return:
    """
    obj = models.UserInfo.objects.filter(id=pk).first()
    if not obj:
        return HttpResponse('角色不存在')

    if request.method == 'GET':
        form = UpdateUserModelForm(instance=obj)
        return render(request, 'rbac/change.html', {'form': form})

    form = UpdateUserModelForm(instance=obj, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(reverse('rbac:user_list'))
    return render(request, 'rbac/change.html', {'form': form})


def user_del(request, pk):
    """
    用户删除
    :param request:
    :param pk:要被删除的用户id
    :return:
    """
    origin_url = reverse('rbac:user_list')
    if request.method == "GET":
        return render(request, 'rbac/delete.html', {'cancel_url': origin_url})

    models.UserInfo.objects.filter(id=pk).delete()
    return redirect(origin_url)


def user_reset_pwd(request, pk):
    """
    重置密码
    :param request:
    :param pk:
    :return:
    """
    obj = models.UserInfo.objects.filter(id=pk).first()
    if not obj:
        return HttpResponse('角色不存在')

    if request.method == 'GET':
        form = ResetPasswordUserModelForm()
        return render(request, 'rbac/change.html', {'form': form})

    form = ResetPasswordUserModelForm(instance=obj, data=request.POST)
    if form.is_valid():
        form.save()
        return redirect(reverse('rbac:user_list'))
    return render(request, 'rbac/change.html', {'form': form})