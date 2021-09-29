from types import FunctionType
import functools
from django.db.models import ForeignKey, ManyToManyField
from django.http import  QueryDict
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import HttpResponse, render, redirect
from django.db.models import Q
from django import forms

from stark.utils.pagination import Pagination

def get_choice_text(title, field):
    """
    对于stark组件中，自定义列时，choice字段如果想显示中文信息，调用此方法
    :param title: 希望页面显示得表头
    :param field: 字段名称
    :return:
    """
    def inner(self, obj=None, is_header=None):
        if is_header:
            return title
        method = "get_{}_display".format(field)

        return getattr(obj, method)()

    return inner


def get_datetime_text(title, field, time_format='%Y-%m-%d'):
    """
    格式化时间
    :param title:
    :param field:
    :return:
    """
    def inner(self, obj=None, is_header=None):
        if is_header:
            return title
        datetime_value = getattr(obj, field)

        return datetime_value.strftime(time_format)

    return inner


def get_m2m_text(title, field):
    """
    多对多文本内容
    :param title:
    :param field:
    :return:
    """
    def inner(self, obj=None, is_header=None):
        if is_header:
            return title
        queryset = getattr(obj, field).all()
        text_list = [str(row) for row in queryset]
        return ",".join(text_list)

    return inner



class SearchGroupRow(object):
    def __init__(self, title, queryset_or_tuple, option, query_dict):
        """
        接收的是一个元组或者queryset对象
        :param title: 组合搜索列名称
        :param queryset_or_tuple: 组合搜索关联获取到的数据
        :param option: 配置
        :param query_dict: request.GET
        """
        self.title = title
        self.queryset_or_tuple = queryset_or_tuple
        self.option = option
        self.query_dict = query_dict

    def __iter__(self):
        yield '<div class="whole">'
        yield self.title
        yield '</div>'

        yield '<div class="others">'
        total_query_dict = self.query_dict.copy()
        total_query_dict._mutable = True

        origin_value_list = self.query_dict.getlist(self.option.field)
        if not origin_value_list:
            yield "<a href='?{}' class='active'>全部</a>".format(total_query_dict.urlencode())
        else:
            total_query_dict.pop(self.option.field)
            yield "<a href='?{}'>全部</a>".format(total_query_dict.urlencode())
        for item in self.queryset_or_tuple:
            text = self.option.get_text(item)
            value = str(self.option.get_value(item))
            query_dict = self.query_dict.copy()
            query_dict._mutable = True

            # 在保留原来参数的前提下，将每个按钮对应参数和原有参数组合起来，生成该按钮的url
            if not self.option.is_multi:
                # 不支持多选
                query_dict[self.option.field] = value
                if value in origin_value_list:
                    query_dict.pop(self.option.field)
                    yield "<a href='?{}' class='active'>{}</a>".format(query_dict.urlencode(), text)
                else:
                    yield "<a href='?{}'>{}</a>".format(query_dict.urlencode(), text)
            else:
                # 支持多选
                multi_value_list = query_dict.getlist(self.option.field)
                if value in multi_value_list:
                    multi_value_list.remove(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield "<a href='?{}' class='active'>{}</a>".format(query_dict.urlencode(), text)
                else:
                    multi_value_list.append(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield "<a href='?{}'>{}</a>".format(query_dict.urlencode(), text)

        yield '</div>'


class Option(object):
    def __init__(self, field, is_multi=False, db_condition=None, text_func=None, value_func=None):
        """
        替代列表套字典的形式，字典的key容易写错，导致出问题
        :param field: 组合搜索关联的字段
        :param is_multi: 是否支持多选
        :param db_condition: 数据库关联查询时的条件
        :param text_func: 是个函数对象，用于用户自定制获取组合搜索关键字按钮显示的文本内容
        :param value_func: 是个函数对象，用于用户自定制获取组合搜索关键字按钮显示的文本内容背后的值
        """
        self.field = field
        self.is_multi = is_multi
        self.db_condition = db_condition
        if not db_condition:
            self.db_condition = {}

        self.text_func = text_func
        self.value_func = value_func

        self.is_choice = False  # 用来判断当前对象中存储的数据是否为choice数据

    def get_db_condition(self, request, *args, **kwargs):
        return self.db_condition

    def get_queryset_or_tuple(self, model_class, request, *args, **kwargs):
        """
        根据字段获取数据库关联的数据
        :return:
        """
        # 根据字符串拿到字段对象
        field_object = model_class._meta.get_field(self.field)
        # 拿到字段对象的中文描述信息
        title = field_object.verbose_name

        # FK MTM choice 的不同处理
        if isinstance(field_object, ForeignKey) or isinstance(field_object, ManyToManyField):
            # 关联字段的处理，拿到其关联字段的所有内容
            db_condition = self.get_db_condition(request, *args, **kwargs)
            return SearchGroupRow(title, field_object.rel.model.objects.filter(**db_condition), self, request.GET)
        else:
            # choice的处理
            self.is_choice = True
            return SearchGroupRow(title, field_object.choices, self, request.GET)

    def get_text(self, field_object):
        """
        获取文本的函数
        :param field_object:
        :return:
        """
        if self.text_func:
            return self.text_func(field_object)

        if self.is_choice:
            return field_object[1]
        return str(field_object)

    def get_value(self, field_object):
        """
        获取文本背后的值
        :param fiedl_object:
        :return:
        """
        if self.value_func:
            return self.value_func(field_object)

        if self.is_choice:
            return field_object[0]
        return field_object.pk

class StarkHandle(object):
    """
    处理请求的视图函数所在的类,公共类
    """
    display_list = []

    per_page_count = 10  # 每页展示的数据条数

    is_has_add_btn = True  # 用来判断是否有添加按钮

    order_list = []  # 设定排序的规则

    search_list = []  # 设定搜索规则

    def __init__(self, site, model_class, prev):
        self.site = site
        self.model_class = model_class
        self.prev = prev
        self.request = None

    def get_add_btn(self):
        """
        预留的获取添加按钮，用户可以自定义来决定按钮的链接和样式，通过is_has_add_btn来决定页面是否展示按钮
        :return:
        """
        if self.is_has_add_btn:
            return '<a href="{}" class="btn btn-primary">添加</a>'.format(self.reverse_add_url())

        return None

    def reverse_commons_url(self, name, *args, **kwargs):
        """
        保存原搜索条件的反向解析函数
        :param name: url的别名
        :param args:
        :param kwargs:
        :return:
        """
        name = '{}:{}'.format(self.site.namespace, name)
        base_url = reverse(name, args=args, kwargs=kwargs)
        if not self.request.GET:
            # 没有原搜索条件，在第一页直接点击的添加按钮
            dst_url = base_url
        else:
            # 有携带搜索条件
            params = self.request.GET.urlencode()
            query_dict = QueryDict(mutable=True)
            query_dict['_filter'] = params
            dst_url = '{}?{}'.format(base_url, query_dict.urlencode())
        return dst_url

    def reverse_add_url(self, *args, **kwargs):
        """
        返回带有原搜索条件的添加url
        :return:
        """
        return self.reverse_commons_url(self.get_add_url_name, *args, **kwargs)

    def reverse_change_url(self, *args, **kwargs):
        """
        返回反向解析后的编辑的url，有原搜索条件的话携带
        :return:
        """
        return self.reverse_commons_url(self.get_change_url_name, *args, **kwargs)

    def reverse_del_url(self, *args, **kwargs):
        """
        返回反向解析后的编辑的url，有原搜索条件的话携带
        :return:
        """
        return self.reverse_commons_url(self.get_delete_url_name, *args, **kwargs)

    def reverse_list_url(self):
        """
        跳转回列表页面时，生成的url，解析存储在request的原搜索条件
        :return:
        """
        params = self.request.GET.get('_filter')
        name = "{}:{}".format(self.site.namespace, self.get_list_url_name)
        base_url = reverse(name)
        if not params:
            return base_url
        return "{}?{}".format(base_url, params)

    def display_checkbox(self, obj=None, is_header=None):
        """
        定义一列数据，checkbox选择框
        :param obj:
        :param is_header:
        :return:
        """
        if is_header:
            return "选择"

        return mark_safe('<input type="checkbox" name="pk" value="{}">'.format(obj.pk))

    def display_edit(self, obj=None, is_header=None):
        """
        自定义列表展示页的某一列数据，在列表页面展示除数据库表外的数据，如：编辑按钮
        :param obj: 要操作的模型类实例化对象，一个模型类实例化对象对应的是数据库中的一行数据
        :param is_header: 一列有表头和数据两种，用于判断是返回表格数据还是表头数据
        :return:
        """
        if is_header:
            return "编辑表头"

        return mark_safe('<a href="{}">编辑</a>'.format(self.reverse_change_url(pk=obj.pk)))

    def display_del(self, obj=None, is_header=None):
        """
        自定义列表展示页的某一列数据，在列表页面展示除数据库表外的数据，如：编辑按钮
        :param obj: 要操作的模型类实例化对象，一个模型类实例化对象对应的是数据库中的一行数据
        :param is_header: 一列有表头和数据两种，用于判断是返回表格数据还是表头数据
        :return:
        """
        if is_header:
            return "删除表头"

        return mark_safe('<a href="{}">删除</a>'.format(self.reverse_del_url(pk=obj.pk)))

    def display_edit_and_del(self, obj=None, is_header=None):
        """
        删除和修改列
        :param obj:
        :param is_header:
        :return:
        """
        if is_header:
            return "操作"

        return mark_safe('<a href="{}">编辑</a> <a href="{}">删除</a>'.format(
            self.reverse_change_url(pk=obj.pk),
            self.reverse_del_url(pk=obj.pk))
        )

    def get_display_list(self):
        """
        获取页面上应该显示的列，用户集成该类，可以做显示列的自定义扩展： 根据用户的不同显示不同的列
        :return:
        """
        value = []
        value.extend(self.display_list)

        return value

    def get_order_list(self):
        """
        获取排序规则的顺序列表
        :return:
        """
        return self.order_list or ['-id', ]

    def get_search_list(self):
        """
        获取搜索的规则，对哪些列进行哪些规则的搜索
        :return:
        """
        return self.search_list

    def action_multi_delete(self, request, *args, **kwargs):
        """
        批量删除，如果想在执行完批量删除后跳转到其他页面，可以在此函数中返回redirect()
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(pk__in=pk_list).delete()

    # 用于前端的展示中文字符
    action_multi_delete.text = "批量删除"

    action_list = []

    def get_action_list(self):
        """
        获取用户自定义的批量操作下拉框中展示的选项
        :return:
        """
        return self.action_list

    search_group = []

    def get_search_group(self):
        return self.search_group

    def get_search_group_condition(self, request):
        """
        获取组合搜索的条件
        :param request:
        :return:
        """
        condition = {}
        for option in self.get_search_group():
            if option.is_multi:
                value_list = request.GET.getlist(option.field)
                if not value_list:
                    continue
                condition['{}__in'.format(option.field)] = value_list
            else:
                # 不支持多选的条件
                value = request.GET.get(option.field)
                if not value:
                    continue
                condition[option.field] = value
        return condition

    def change_list_view(self, request, *args, **kwargs):
        # 获取下拉框选项
        action_list = self.get_action_list()
        action_dict = {action.__name__: action.text for action in action_list}
        if request.method == "POST":
            func_name = request.POST.get('action')
            if func_name and func_name in action_dict:
                # 用户选中了批量操作，并且该操作在字典中，执行该函数
                func_response = getattr(self, func_name)(request, *args, **kwargs)
                if func_response:
                    # 用于定制化，执行完批量操作之后的跳转
                    return func_response

        # 获取排序
        order_list = self.get_order_list()

        # 组合搜索条件
        search_group_condition = self.get_search_group_condition(request)

        # 搜索关键字
        search_value = request.GET.get('q', '')
        conn = Q()  # 构造多个条件 ‘或’ 查询
        conn.connector = "OR"
        search_list = self.get_search_list()
        if search_value:
            for search in search_list:
                conn.children.append((search, search_value))

        header_list = []
        display_list = self.get_display_list()  # 通过get_display_list方法拿到要展示的数据，如果用户继承此类并重写了此方法就会调用子类中的该方法，达到扩展的目的
        if display_list:
            for key_or_func in display_list:
                if isinstance(key_or_func, FunctionType):
                    # 是函数对象，调用该函数，将返回值作为表头内容
                    verbose_name = key_or_func(self, is_header=True)
                else:
                    verbose_name = self.model_class._meta.get_field(key_or_func).verbose_name
                header_list.append(verbose_name)
        else:
            # 用户没有继承这个类和重新给display_list赋值，使用当前类中的display_list
            # 表头信息为该表名称
            header_list.append(self.model_class._meta.model_name)

        query_set = self.model_class.objects.filter(conn).filter(**search_group_condition).order_by(*order_list)  # 获取排序之后的数据
        # 分页器初始化
        all_count = query_set.count()
        query_params = request.GET.copy()  # 都是默认不可修改的
        query_params._mutable = True  # 设置之后，query_params可以修改

        pager = Pagination(
            current_page=request.GET.get('page'),
            all_count=all_count,
            base_url=request.path_info,
            query_params=query_params,
            per_page=self.per_page_count,
        )
        # 对数据库中的值进行切片，拿到当前页面展示的数据内容
        data_list = query_set[pager.start:pager.end]

        body_list = []  # 构造出给前端使用的数据结构，包含该表中那个的所有数据
        """
            body_list = [
                ['胡说', '17', 'hushuo@qq.com'],  # 数据表中的一行数据
                ['呼哈', '32', 'huha@qq.com']
            ]
        """
        for item in data_list:
            # 构造一行数据
            row_list = []
            if display_list:
                for key_or_func in display_list:
                    if isinstance(key_or_func, FunctionType):
                        row_list.append(key_or_func(self, obj=item, is_header=False))
                    else:
                        row_list.append(getattr(item, key_or_func))
            else:
                # 展示对象信息到页面
                row_list.append(item)

            body_list.append(row_list)

        # 组合查询
        search_group = self.get_search_group()
        search_group_row_list = []
        for option_object in search_group:
            # 根据字符串拿到 字段对象
            row = option_object.get_queryset_or_tuple(self.model_class, request, *args, **kwargs)
            print(option_object.field, row)
            search_group_row_list.append(row)

        return render(
            request,
            'stark/change_list.html',
            {
                'header_list': header_list,
                'body_list': body_list,
                'pager': pager,
                'add_button': self.get_add_btn(),
                'search_list': search_list,
                'search_value': search_value,
                'action_dict': action_dict,
                'search_group_row_list': search_group_row_list,
            }
        )

    model_form_class = None  # 支持用户扩展xxx modelform的内容，比如增加一个密码的二次确认输入框

    def get_model_form_class(self, add_or_change=None):
        """
        扩展用户定制功能，给增加和编辑页面范湖不同的ModelForm,
        默认是，用户修改model_form_class的值，使用同一个ModelForm
        用户继承重写该方法，根据参数add_or_change的不同返回不同的ModelForm
        :param add_or_change: 有两搁值判断 "add"  表示是增加 "change" 表示是编辑
        :return:
        """
        if self.model_form_class:
            return self.model_form_class

        from stark.forms.base import BootStrapModelForm

        class DynamicModelForm(BootStrapModelForm):
            class Meta:
                model = self.model_class
                fields = '__all__'

        return DynamicModelForm

    def save(self, request, form, is_update, *args, **kwargs):
        """
        保存前端传递过来的数据, 用户可以通过重写这个方法来在保存前给某些字段设置默认值
        :param request:
        :param form:
        :param is_update:
        :return:
        """
        form.save()

    def add_view(self, request, *args, **kwargs):
        model_form_class = self.get_model_form_class("add")
        form = model_form_class()
        if request.method == "GET":
            return render(request, 'stark/change.html', {'form':form})
        form = model_form_class(data=request.POST)
        if form.is_valid():
            self.save(request, form, False, *args, **kwargs)
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    def change_view(self, request, pk, *args, **kwargs):
        obj = self.model_class.objects.filter(pk=pk).first()
        model_form_class = self.get_model_form_class("change")
        if not obj:
            return HttpResponse("信息不存在")

        if request.method == "GET":
            form = model_form_class(instance=obj)
            return render(request, 'stark/change.html', {'form': form})

        form = model_form_class(data=request.POST, instance=obj)
        if form.is_valid():
            self.save(request, form, True, *args, **kwargs)
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    def delete_view(self, request, pk, *args, **kwargs):
        origin_url = self.reverse_list_url()
        if request.method == "GET":
            return render(request, 'stark/delete.html', {'cancel_url': origin_url})

        self.model_class.objects.filter(pk=pk).delete()
        return redirect(origin_url)

    def get_url_name(self, param):
        app_label, model_name = self.model_class._meta.app_label, self.model_class._meta.model_name
        if self.prev:
            return "{}_{}_{}_{}".format(app_label, model_name, self.prev, param)

        return "{}_{}_{}".format(app_label, model_name, param)

    @property
    def get_list_url_name(self):
        """
        获取列表页面url的name
        :return:
        """
        return self.get_url_name('list')

    @property
    def get_add_url_name(self):
        """
        获取新增页面url的name
        :return:
        """
        return self.get_url_name('add')

    @property
    def get_change_url_name(self):
        """
        获取修改页面url的name
        :return:
        """
        return self.get_url_name('change')

    @property
    def get_delete_url_name(self):
        """
        获取删除页面url的name
        :return:
        """
        return self.get_url_name('delete')

    def wrapper(self, func):
        """
        定义一个装饰器，用来装饰视图函数，增加视图函数执行前，将request赋值到类对象中，方便后续其他方法的使用request对象
        :param func:
        :return:
        """
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            self.request = request
            return func(request, *args, **kwargs)
        return inner

    def get_urls(self):
        patterns = [
            url(r'^list/$', self.wrapper(self.change_list_view), name=self.get_list_url_name),
            url(r'^add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'^change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            url(r'^delete/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name),
        ]
        patterns.extend(self.extra_urls())
        return patterns

    def extra_urls(self):
        return []

class StarkSite(object):
    def __init__(self):
        self._registry = []
        self.name = 'stark'
        self.namespace = 'stark'

    def get_urls(self):
        urls = []
        for item in self._registry:
            model_class = item.get('model_class')
            handle = item.get('handle')
            prev = item.get('prev')
            app_label, model_name = model_class._meta.app_label, model_class._meta.model_name
            if prev:
                # 在做一层路由分发
                urls.append(url(r'^{}/{}/{}/'.format(app_label, model_name, prev), (handle.get_urls(), None, None)))
            else:
                urls.append(url(r'^{}/{}/'.format(app_label, model_name), (handle.get_urls(), None, None)))
        return urls

    @property
    def urls(self):
        return self.get_urls(), self.name, self.namespace

    def register(self, model_class, handle_class=StarkHandle, prev=None):
        """

        :param model_class: models中数据库表对应的类
        :param handle_class: 处理请求的视图函数所在的类
        :param prev: 生成url的前缀
        :return:
        """
        self._registry.append({'model_class': model_class, 'handle': handle_class(self, model_class, prev), 'prev': prev})

site = StarkSite()
