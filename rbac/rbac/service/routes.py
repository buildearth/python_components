import re
from collections import OrderedDict
from django.conf import settings
from django.utils.module_loading import import_string
from django.urls import RegexURLResolver, RegexURLPattern

def check_url_exclude(url):
    """
    排除一些特定的url
    :param url:
    :return:
    """
    for regex in settings.AUTO_DISCOVER_EXCLUDE:
        if re.match(regex, url):
            return True


def recursion_urls(pre_namespace, pre_url, urlpatterns, url_orderd_dict):
    """
    递归的去获取url
    :param pre_namespace: namespace前缀，用于拼接name做反向解析
    :param pre_url: url的前缀，用于拼接url
    :param urlpatterns: 路由关系列表
    :param url_orderd_dict: 用于保存递归中获取的所有路由
    :return:
    """
    for item in urlpatterns:
        if isinstance(item, RegexURLPattern):  # 非路由分发
            # 路由添加到字典中
            if not item.name:
                continue
            # 有name才继续添加
            if pre_namespace:
                name = '{}:{}'.format(pre_namespace, item.name)
            else:
                name = item.name
            url = pre_url + item._regex  # 此时拼接完的样子：/^rbac/^user/edit/(?P<pk>\d+)/$, 不符合希望，需去掉起始和终止符
            url = url.replace('^', '').replace('$', '')
            if check_url_exclude(url):  # 是否保存的url，白名单check
                continue
            # 保存数据
            url_orderd_dict[name] = {'name': name, 'url': url}
        elif isinstance(item, RegexURLResolver):  # 路由分发，进行递归操作
            # namespace 有前缀也是需要拼接的，多级分发下会有多级的namespace, namespace考虑多种情况
            if pre_namespace:
                if item.namespace:
                    # 上一级存在namespace,当前url也有namespace
                    namespace = '{}:{}'.format(pre_namespace, item.namespace)
                else:
                    # 上一级存在namespace, 当前路由分发没有namespace，使用上级的namespace
                    namespace = pre_namespace
            else:
                if item.namespace:
                    # 上一级没有namespace,当前有namespace,使用当前的namesapce
                    namespace = item.namespace
                else:
                    # 上一级和当前都没有namespace,就没有namespace
                    namespace = None

            recursion_urls(namespace, pre_url + item.regex.pattern, item.url_patterns, url_orderd_dict)


def get_all_url_dict():
    """
    获取那些有name别名的url
    :return:
    """
    url_odered_dict = OrderedDict()
    '''
        {
            'rbac:menu_list' : {name:'menu_list', url:'xx/menu/list'}
        }
        如果没有写name，是不会保存的。
    '''

    # import_string(settings.ROOT_URLCONF)  # 相当于 from xxx import urls
    md = import_string(settings.ROOT_URLCONF)
    print(md.urlpatterns)
    recursion_urls(None, '/', md.urlpatterns, url_odered_dict)

    return url_odered_dict
