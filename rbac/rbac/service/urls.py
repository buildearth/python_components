from django.urls import reverse
from django.http import QueryDict


def memory_url(request, name, *args, **kwargs):
    """
    生成带有原搜索条件的url，替代了原来模板中的url
    :param request:
    :param name:
    :return:
    """
    basic_url = reverse(name, args=args, kwargs=kwargs)  # reverse带参数的反向解析
    # 对原url是有 ?xxx 携带参数进行判断，有参数进行拼接
    if request.GET:
        # 拼接
        query_dict = QueryDict(mutable=True)
        query_dict['_filter'] = request.GET.urlencode()

        return '{}?{}'.format(basic_url, query_dict.urlencode())
    return basic_url

def memory_reverse(request, name, *args, **kwargs):
    """
    反向生成url
    在url中将原搜索条件获取，拼接返回
    :param request:
    :param name:
    :param args:
    :param kwargs:
    :return:
    """
    basic_url = reverse(name, args=args, kwargs=kwargs)
    origin_url = request.GET.get('_filter')
    if origin_url:
        basic_url = "{}?{}".format(basic_url, origin_url)
    return basic_url
